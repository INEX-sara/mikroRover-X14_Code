from machine import Pin, PWM
import rp2
import time

# --- การตั้งค่าคงที่ ---
UART_PIN   = 12    # ขา D3 (GPIO 12) ที่ใช้รับสัญญาณจากรีโมต
BAUD_RATE  = 9600  # ความเร็วในการส่งข้อมูล 

# --- การตั้งค่าเซอร์โวมอเตอร์ (Servo Setup) ---
# สร้างออบเจกต์ PWM สำหรับเซอร์โว 2 ตัว
sv1 = PWM(Pin(18)) # Servo 1 ต่อที่ขา 18 (ช่อง SV1)
sv2 = PWM(Pin(19)) # Servo 2 ต่อที่ขา 19 (ช่อง SV2)

# กำหนดความถี่เป็น 50Hz 
sv1.freq(50)        
sv2.freq(50)       

# --- ฟังก์ชันแปลงมุมเป็นสัญญาณ PWM ---
def set_servo(servo, angle):
    # สูตรแปลงมุม 0-180 องศา เป็นค่า Duty Cycle (หน่วยนาโนวินาที)
    # ค่า 500,000ns (0.5ms) = 0 องศา
    # ค่า 2,500,000ns (2.5ms) = 180 องศา
    duty = 500_000 + int(angle * 2_000_000 // 180)
    servo.duty_ns(duty)

# --- ตารางจับคู่ปุ่มกด ---
BUTTONS = {
    # กลุ่มควบคุม Servo 1 
    0x0009: "L1",  0x0005: "L2",   
    # กลุ่มควบคุม Servo 2 
    0x0801: "R1",  0x0401: "R2"   
}

# --- โปรแกรม PIO สำหรับรับค่า UART ---
@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, autopush=True, push_thresh=8)
def uart_rx():
    wait(0, pin, 0)      # รอสัญญาณ Start Bit (Low)
    set(x, 7) [10]       # ตั้งตัวนับ 8 บิต
    label("b")           # จุดวนลูปอ่านข้อมูล
    in_(pins, 1)         # อ่านค่า 1 บิต
    nop() [5]            # รอเวลาให้ตรงกับ Baudrate
    jmp(x_dec, "b")      # วนลูปจนครบ 8 บิต

# เริ่มการทำงานของ State Machine (SM)
sm = rp2.StateMachine(0, uart_rx, freq=8*BAUD_RATE, in_base=Pin(UART_PIN, Pin.IN, Pin.PULL_UP))
sm.active(1)

# ตัวแปรสำหรับเก็บข้อมูล
b1, wait = 0, 1
angle1 = 90  # มุมเริ่มต้นของ Servo 1 (90 องศา)
angle2 = 90  # มุมเริ่มต้นของ Servo 2 (90 องศา)

# สั่งให้เซอร์โวหมุนไปที่ตำแหน่งเริ่มต้นทันที
set_servo(sv1, angle1)
set_servo(sv2, angle2)
print("Double Servo Test: Ready!")

# --- ลูปการทำงานหลัก ---
while True:
    # ตรวจสอบว่ามีข้อมูลส่งมาจากรีโมตหรือไม่
    if sm.rx_fifo():
        data = sm.get() & 0xFF # อ่านข้อมูลมา 1 ไบต์
        
        if wait: 
            b1 = data; wait = 0 # เก็บไบต์แรกไว้ก่อน
        else:
            # นำไบต์แรกและไบต์สองมารวมกันเป็นรหัส 16 บิต
            code = (b1 << 8) | data
            name = BUTTONS.get(code) # แปลงรหัสเป็นชื่อปุ่ม
            wait = 1 # รีเซ็ตสถานะเพื่อรอรับรอบถัดไป
            
            if name: # ถ้ากดปุ่มที่เรารู้จัก
                print(f"Pressed: {name}")
                
                # --- ควบคุม Servo 1 ด้วยปุ่ม L1/L2 ---
                if name == "L1":
                    angle1 = angle1 + 1  # กด L1 เพิ่มมุม Servo 1
                elif name == "L2":
                    angle1 = angle1 - 1  # กด L2 ลดมุม Servo 1
                
                # --- ควบคุม Servo 2 ด้วยปุ่ม R1/R2 ---
                elif name == "R1":
                    angle2 = angle2 + 1  # กด R1 เพิ่มมุม Servo 2
                elif name == "R2":
                    angle2 = angle2 - 1  # กด R2 ลดมุม Servo 2
                
                # --- ระบบป้องกัน (Clamping) ---
                # จำกัดค่าไม่ให้เกิน 0-180 องศา เพื่อป้องกันเฟืองแตก
                if angle1 > 180: angle1 = 180
                if angle1 < 0:   angle1 = 0
                if angle2 > 180: angle2 = 180
                if angle2 < 0:   angle2 = 0
                
                # --- ส่งคำสั่งไปที่มอเตอร์ ---
                # อัปเดตตำแหน่งของเซอร์โวทั้งสองตัวพร้อมกัน
                set_servo(sv1, angle1) 
                set_servo(sv2, angle2) 
                
                # แสดงค่ามุมปัจจุบันทางหน้าจอ
                print(f"SV1: {angle1} | SV2: {angle2}")
