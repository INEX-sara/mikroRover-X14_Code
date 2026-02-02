from machine import Pin, PWM
import rp2
import time
UART_PIN   = 12    
BAUD_RATE  = 9600
sv1 = PWM(Pin(18)) # เซอร์โว 1
sv2 = PWM(Pin(19)) # เซอร์โว 2 
sv1.freq(50)       
sv2.freq(50)      
def set_servo(servo, angle):
    # สูตรแปลงมุม 0-180 เป็นสัญญาณ PWM
    duty = 500_000 + int(angle * 2_000_000 // 180)
    servo.duty_ns(duty)
BUTTONS = {
    0x0009: "L1",  0x0005: "L2",  
    0x0801: "R1",  0x0401: "R2"   
@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, autopush=True, push_thresh=8)
def uart_rx():
    wait(0, pin, 0); set(x, 7) [10]; label("b")
    in_(pins, 1); nop() [5]; jmp(x_dec, "b")
sm = rp2.StateMachine(0, uart_rx, freq=8*BAUD_RATE, in_base=Pin(UART_PIN, Pin.IN, Pin.PULL_UP))
sm.active(1)
b1, wait = 0, 1
angle1 = 90  # มุมของ Servo 1
angle2 = 90  # มุมของ Servo 2
set_servo(sv1, angle1)
set_servo(sv2, angle2)
print("Double Servo Test: Ready!")
while True:
    if sm.rx_fifo():
        data = sm.get() & 0xFF
        if wait: 
            b1 = data; wait = 0
        else:
            code = (b1 << 8) | data
            name = BUTTONS.get(code)
            wait = 1
            if name:
                print(f"Pressed: {name}")
                # --- [ส่วนที่ 1] ควบคุม Servo 1 (L1/L2) ---
                if name == "L1":
                    angle1 = angle1 + 5
                elif name == "L2":
                    angle1 = angle1 - 5
                # --- [ส่วนที่ 2] ควบคุม Servo 2 (R1/R2) ---
                elif name == "R1":
                    angle2 = angle2 + 5  # เพิ่มมุม Servo 2
                elif name == "R2":
                    angle2 = angle2 - 5  # ลดมุม Servo 2
                # --- ระบบป้องกัน (Clamping) ---
                # ต้องเช็คแยกกัน เพราะมุมของใครของมัน
                if angle1 > 180: angle1 = 180
                if angle1 < 0:   angle1 = 0
                if angle2 > 180: angle2 = 180
                if angle2 < 0:   angle2 = 0
                # --- ส่งคำสั่งไปที่มอเตอร์ ---
                set_servo(sv1, angle1) # สั่ง Servo 1
                set_servo(sv2, angle2) # สั่ง Servo 2
                print(f"SV1: {angle1} | SV2: {angle2}")
