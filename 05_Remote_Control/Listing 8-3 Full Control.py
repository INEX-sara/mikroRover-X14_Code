from machine import Pin, PWM
import rp2
import time

# --- การตั้งค่าคงที่ ---
UART_PIN   = 12    # ขา D3 (GPIO 12) สำหรับรับสัญญาณจากรีโมต
BAUD_RATE  = 9600  # ความเร็วการส่งข้อมูล (Baud rate)
TIMEOUT_MS = 150   # ระยะเวลา Safety (ถ้าสัญญาณเงียบเกิน 0.15 วิ ให้หยุด)
SPEED      = 60    # ความเร็วในการเคลื่อนที่ (0-100)

# --- การตั้งค่ามอเตอร์ (Motor Setup) ---
# กำหนดขา PWM ให้มอเตอร์ซ้าย (m1) และขวา (m2)
m1a = PWM(Pin(13)); m1a.freq(1000) 
m1b = PWM(Pin(14)); m1b.freq(1000)
m2a = PWM(Pin(16)); m2a.freq(1000)
m2b = PWM(Pin(17)); m2b.freq(1000)

# --- ฟังก์ชันควบคุมมอเตอร์ ---

# ฟังก์ชันแปลงค่า 0-100 เป็นค่า Duty Cycle (0-65535)
def set_speed(pin, value):
    duty = int(max(0, min(100, value)) * 655.35)
    pin.duty_u16(duty)

# ฟังก์ชันสั่งหยุด (ตัดไฟมอเตอร์ทุกตัว)
def stop():
    m1a.duty_u16(0); m1b.duty_u16(0)
    m2a.duty_u16(0); m2b.duty_u16(0)

# ฟังก์ชันเดินหน้า (Forward)
def forward(s):
    # ล้อซ้ายเดินหน้า, ล้อขวาเดินหน้า
    m1a.duty_u16(0); set_speed(m1b, s) 
    m2a.duty_u16(0); set_speed(m2b, s)

# ฟังก์ชันถอยหลัง (Backward)
def backward(s):
    # ล้อซ้ายถอยหลัง, ล้อขวาถอยหลัง (สลับขั้วจ่ายไฟ)
    set_speed(m1a, s); m1b.duty_u16(0)
    set_speed(m2a, s); m2b.duty_u16(0)

# ฟังก์ชันหมุนซ้าย (Spin Left)
def turn_left(s):
    # เทคนิคการหมุนตัว: ล้อซ้ายถอย + ล้อขวาหน้า
    set_speed(m1a, s); m1b.duty_u16(0) 
    m2a.duty_u16(0); set_speed(m2b, s) 

# ฟังก์ชันหมุนขวา (Spin Right)
def turn_right(s):
    # เทคนิคการหมุนตัว: ล้อซ้ายหน้า + ล้อขวาถอย
    m1a.duty_u16(0); set_speed(m1b, s) 
    set_speed(m2a, s); m2b.duty_u16(0) 

# --- ตารางจับคู่ปุ่มกด (Button Map) ---
BUTTONS = {
    0x0011: "LU",  # (เดินหน้า)
    0x0081: "LD",  # (ถอยหลัง)
    0x0021: "LL",  # (เลี้ยวซ้าย)
    0x0041: "LR"   # (เลี้ยวขวา)
}

# --- โปรแกรม PIO สำหรับรับค่า UART ---
@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, autopush=True, push_thresh=8)
def uart_rx():
    wait(0, pin, 0)      # รอสัญญาณ Start Bit
    set(x, 7) [10]       # ตั้งตัวนับ 8 บิต
    label("b")           # จุดเริ่มลูป
    in_(pins, 1)         # อ่าน 1 บิต
    nop() [5]            # หน่วงเวลาให้ตรงจังหวะ
    jmp(x_dec, "b")      # วนลูปจนครบ

# เริ่มการทำงานของ PIO State Machine
sm = rp2.StateMachine(0, uart_rx, freq=8*BAUD_RATE, in_base=Pin(UART_PIN, Pin.IN, Pin.PULL_UP))
sm.active(1)
print("Ready! Full Control")

# ตัวแปรช่วยประมวลผล
b1, wait = 0, 1          # ตัวแปรเก็บไบต์แรก และสถานะการรอ
press = 0                # สถานะว่ามีการกดปุ่มอยู่หรือไม่
last = time.ticks_ms()   # เวลาล่าสุดที่ได้รับข้อมูล

# --- ลูปการทำงานหลัก ---
while True:
    now = time.ticks_ms()

    # [ระบบ Safety] ถ้าเวลานิ่งไปเกิน 0.15 วิ ให้สั่งหยุดรถ
    if press and time.ticks_diff(now, last) > TIMEOUT_MS:
        stop()
        press = 0

    # ตรวจสอบว่ามีข้อมูลเข้ามาหรือไม่
    if sm.rx_fifo():
        data = sm.get() & 0xFF  # อ่านข้อมูล 1 ไบต์
        last = now              # อัปเดตเวลาล่าสุด (รีเซ็ต Safety Timer)
        
        if wait: 
            b1 = data; wait = 0 # ถ้าเป็นไบต์แรก เก็บไว้ก่อน
        else:
            # รวมไบต์ 1 และ 2 เป็นรหัสเต็ม (16-bit)
            code = (b1 << 8) | data
            name = BUTTONS.get(code, "Unknown") # แปลรหัสเป็นชื่อปุ่ม
            wait = 1 # เตรียมรอรับชุดต่อไป
            
            if name != "Unknown":
                press = 1 # ระบุว่ามีการกดปุ่ม
                
                # ตรวจสอบชื่อปุ่มแล้วสั่งงานฟังก์ชันที่เกี่ยวข้อง
                if   name == "LU": forward(SPEED)     # เดินหน้า
                elif name == "LD": backward(SPEED)    # ถอยหลัง
                elif name == "LL": turn_left(SPEED)   # หมุนตัวซ้าย
                elif name == "LR": turn_right(SPEED)  # หมุนตัวขวา
