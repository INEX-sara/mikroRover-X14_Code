from machine import Pin, PWM
# เรียกใช้ไลบรารีสำหรับเข้าถึงฟังก์ชัน Programmable I/O (PIO) เพื่อสร้าง State Machine ในการจำลองการรับส่งข้อมูลแบบ UART
import rp2 
import time

# ส่วนการตั้งค่าเบื้องต้น
UART_PIN = 12       # ขา D3 สำหรับรับสัญญาณจอย
BAUD_RATE = 9600    # ความเร็วสื่อสาร
TIMEOUT = 150       # เวลาตัดการทำงานเมื่อปล่อยมือ (ms)
SPEED = 60          # ความเร็วหุ่นยนต์ (0-100)

# กำหนดขามอเตอร์
m1a = PWM(Pin(13)); m1a.freq(1000) # มอเตอร์ซ้าย A
m1b = PWM(Pin(14)); m1b.freq(1000) # มอเตอร์ซ้าย B
m2a = PWM(Pin(16)); m2a.freq(1000) # มอเตอร์ขวา A
m2b = PWM(Pin(17)); m2b.freq(1000) # มอเตอร์ขวา B

# ส่วนการคำนวณและสั่งงานมอเตอร์ 
def motor(speed_L, speed_R):
    # คำนวณมอเตอร์ซ้าย
    # สูตรแปลงความเร็ว: เปลี่ยนค่า % (0-100) ให้เป็นค่า Duty Cycle (0-65535)
    duty_L = int(abs(speed_L) * 655.35)
    if speed_L < 0:      # กรณีสั่งเดินหน้า 
        m1a.duty_u16(duty_L); m1b.duty_u16(0)
    elif speed_L > 0:    # กรณีสั่งถอยหลัง
        m1a.duty_u16(0);      m1b.duty_u16(duty_L)
    else:                # กรณีสั่งหยุด
        m1a.duty_u16(0);      m1b.duty_u16(0)

    # คำนวณมอเตอร์ขวา
    # สูตรแปลงความเร็ว: เปลี่ยนค่า % (0-100) ให้เป็นค่า Duty Cycle (0-65535)
    duty_R = int(abs(speed_R) * 655.35)
    if speed_R < 0:      # กรณีสั่งเดินหน้า 
        m2a.duty_u16(duty_R); m2b.duty_u16(0)
    elif speed_R > 0:    # กรณีสั่งถอยหลัง
        m2a.duty_u16(0);      m2b.duty_u16(duty_R)
    else:                # กรณีสั่งหยุด
        m2a.duty_u16(0);      m2b.duty_u16(0)

# ส่วนการเตรียมตัวรับสัญญาณ 
BUTTONS = {
    0x0011:"LU", 0x0021:"LL", 0x0081:"LD", 0x0041:"LR" # รหัสปุ่มทิศทาง
}

@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, autopush=True, push_thresh=8)
def uart_rx():
    wait(0, pin, 0); set(x, 7) [10]; label("b")
    in_(pins, 1); nop() [5]; jmp(x_dec, "b")

sm = rp2.StateMachine(0, uart_rx, freq=8*BAUD_RATE, in_base=Pin(UART_PIN, Pin.IN, Pin.PULL_UP))
sm.active(1)

print(f"Ready! Control on Pin {UART_PIN}")

# --- ส่วนการทำงานหลัก (Main Loop) ---
b1, wait, press, last = 0, 1, 0, time.ticks_ms()

while True:
    now = time.ticks_ms()

    # ตรวจสอบความปลอดภัย (Safety Check)
    # หากไม่มีการกดปุ่มนานเกินกำหนด ให้สั่งหยุดมอเตอร์ทันที
    if press and time.ticks_diff(now, last) > TIMEOUT:
        motor(0, 0)
        print("-> หยุด (ปล่อยมือ)")
        press = 0

    # รับข้อมูลและแปลงผล 
    if sm.rx_fifo():
        data = sm.get() & 0xFF; last = now
        
        if wait: 
            b1 = data; wait = 0
        else:
            code = (b1 << 8) | data
            name = BUTTONS.get(code, "Unknown")
            wait = 1
            
            # ตรวจสอบปุ่มและสั่งเคลื่อนที่
            if code not in (0, 1): # กรองค่าสัญญาณเปล่า
                print(f"กดปุ่ม: {name}")
                press = 1
                
                # สั่งงานตามทิศทาง 
                if   name == "LU": motor(-SPEED, -SPEED)    # เดินหน้า
                elif name == "LD": motor(SPEED, SPEED)      # ถอยหลัง
                elif name == "LL": motor(SPEED, -SPEED)     # หมุนซ้าย
                elif name == "LR": motor(-SPEED, SPEED)     # หมุนขวา
