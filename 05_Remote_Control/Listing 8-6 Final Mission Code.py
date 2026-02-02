from machine import Pin, PWM
import rp2
import time
UART_PIN   = 12    # ขา D3 รับสัญญาณ
BAUD_RATE  = 9600
TIMEOUT_MS = 150   # เวลาความปลอดภัย
SPEED      = 50    # ความเร็วการเดิน
# M1 (ซ้าย), M2 (ขวา)
m1a = PWM(Pin(14)); m1a.freq(1000) 
m1b = PWM(Pin(13)); m1b.freq(1000)
m2a = PWM(Pin(17)); m2a.freq(1000)
m2b = PWM(Pin(16)); m2b.freq(1000)
# --- [B] เซอร์โว (Servos) ---
sv1 = PWM(Pin(18)); sv1.freq(50) # Servo 1
sv2 = PWM(Pin(19)); sv2.freq(50) # Servo 2

def set_speed(pin, value):
    duty = int(max(0, min(100, value)) * 655.35)
    pin.duty_u16(duty)
def stop():
    m1a.duty_u16(0); m1b.duty_u16(0)
    m2a.duty_u16(0); m2b.duty_u16(0)
def fd(s): # เดินหน้า
    set_speed(m1a, s); m1b.duty_u16(0)
    set_speed(m2a, s); m2b.duty_u16(0)
def bk(s): # ถอยหลัง
    m1a.duty_u16(0); set_speed(m1b, s)
    m2a.duty_u16(0); set_speed(m2b, s)
def sl(s): # หมุนซ้าย
    m1a.duty_u16(0); set_speed(m1b, s) # ซ้ายถอย
    set_speed(m2a, s); m2b.duty_u16(0) # ขวาหน้า
def sr(s): # หมุนขวา
    set_speed(m1a, s); m1b.duty_u16(0) # ซ้ายหน้า
    m2a.duty_u16(0); set_speed(m2b, s) # ขวาถอย
  
def set_servo(servo, angle):
    duty = 500_000 + int(angle * 2_000_000 // 180)
    servo.duty_ns(duty)
BUTTONS = {
    # ทิศทาง
    0x0011: "LU", 0x0081: "LD", 0x0021: "LL", 0x0041: "LR",
    # เซอร์โว
    0x0009: "L1", 0x0005: "L2", 
    0x0801: "R1", 0x0401: "R2"
}

@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, autopush=True, push_thresh=8)
def uart_rx():
    wait(0, pin, 0); set(x, 7) [10]; label("b")
    in_(pins, 1); nop() [5]; jmp(x_dec, "b")

sm = rp2.StateMachine(0, uart_rx, freq=8*BAUD_RATE, in_base=Pin(UART_PIN, Pin.IN, Pin.PULL_UP))
sm.active(1)

b1, wait, press, last = 0, 1, 0, time.ticks_ms()

angle1 = 90
angle2 = 90
set_servo(sv1, angle1)
set_servo(sv2, angle2)
while True:
    now = time.ticks_ms()
    if press and time.ticks_diff(now, last) > TIMEOUT_MS:
        stop()
        print("-> หยุด (ปล่อยมือ)")
        press = 0
    if sm.rx_fifo():
        data = sm.get() & 0xFF; last = now
        if wait: 
            b1 = data; wait = 0
        else:
            code = (b1 << 8) | data
            name = BUTTONS.get(code)
            wait = 1
            if name:
                press = 1   
                # --- ขับเคลื่อน ---
                if   name == "LU": fd(SPEED)  # เดินหน้า
                elif name == "LD": bk(SPEED)  # ถอยหลัง
                elif name == "LL": sl(SPEED)  # หมุนซ้าย
                elif name == "LR": sr(SPEED)  # หมุนขวา
                # --- แขนจับ (Servo 1) ---
                elif name == "L1":
                    angle1 = min(180, angle1 + 1) # เพิ่มมุม (ไม่เกิน 180)
                    set_servo(sv1, angle1)
                elif name == "L2":
                    angle1 = max(0, angle1 - 1)   # ลดมุม (ไม่ต่ำกว่า 0)
                    set_servo(sv1, angle1)
                # --- แขนจับ (Servo 2) ---
                elif name == "R1":
                    angle2 = min(180, angle2 + 1)
                    set_servo(sv2, angle2)
                elif name == "R2":
                    angle2 = max(0, angle2 - 1)
                    set_servo(sv2, angle2)
