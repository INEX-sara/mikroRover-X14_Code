from machine import Pin, PWM
import rp2
import time

# --- การตั้งค่าคงที่ ---
UART_PIN   = 12    # ขา D3 (GPIO 12) ที่ใช้รับสัญญาณจากรีโมต
BAUD_RATE  = 9600  # ความเร็วในการส่งข้อมูล

# --- การตั้งค่าเซอร์โวมอเตอร์ (Servo Setup) ---
# สร้างออบเจกต์ PWM ที่ขา 18 (ช่อง SV1 )
sv1 = PWM(Pin(18))

# ตั้งความถี่ PWM เป็น 50Hz 
sv1.freq(50)

# --- ฟังก์ชันแปลงมุมเป็นสัญญาณ PWM ---
def set_servo(servo, angle):
    # สูตรแปลงมุม 0-180 องศา ให้เป็นช่วงเวลา Pulse (Duty Cycle)
    # Servo ต้องการ Pulse กว้างประมาณ 500us ถึง 2500us (หน่วยเป็น nanoseconds)
    # 500,000ns = 0 องศา, 2,500,000ns = 180 องศา
    duty = 500_000 + int(angle * 2_000_000 // 180)
    servo.duty_ns(duty) # สั่งให้ PWM ปล่อยสัญญาณออกไป

# --- ตารางจับคู่ปุ่มกด ---
BUTTONS = {
    0x0009: "L1",  # ปุ่ม L1 (สำหรับเพิ่มมุม)
    0x0005: "L2"   # ปุ่ม L2 (สำหรับลดมุม)
}

# --- โปรแกรม PIO สำหรับรับค่า UART ---
# จำลองการทำงานของ Hardware UART เพื่อรับข้อมูลจากสายสัญญาณ
@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, autopush=True, push_thresh=8)
def uart_rx():
    wait(0, pin, 0)      # รอสัญญาณ Start Bit
    set(x, 7) [10]       # ตั้งตัวนับ 8 บิต
    label("b")           # จุดวนลูป
    in_(pins, 1)         # อ่านค่า 1 บิต
    nop() [5]            # รอจังหวะเวลา (Baudrate timing)
    jmp(x_dec, "b")      # วนลูปจนครบ 8 บิต

# เริ่มการทำงานของ State Machine (SM)
sm = rp2.StateMachine(0, uart_rx, freq=8*BAUD_RATE, in_base=Pin(UART_PIN, Pin.IN, Pin.PULL_UP))
sm.active(1)

# ตัวแปรสำหรับเก็บข้อมูล
b1, wait = 0, 1
current_angle = 90  # กำหนดมุมเริ่มต้นที่ 90 องศา (กึ่งกลาง)

# สั่งให้เซอร์โวหมุนไปที่ 90 องศาทันทีเมื่อเริ่มโปรแกรม
set_servo(sv1, current_angle)
print("Servo Test Ready: Press L1 / L2")

# --- ลูปการทำงานหลัก ---
while True:
    # ตรวจสอบว่ามีข้อมูลใน FIFO หรือไม่
    if sm.rx_fifo():
        data = sm.get() & 0xFF # อ่านข้อมูลออกมา 1 ไบต์
        
        if wait: 
            b1 = data; wait = 0 # เก็บไบต์แรกไว้ก่อน
        else:
            # นำไบต์แรกและไบต์สองมารวมกันเป็นรหัส 16 บิต
            code = (b1 << 8) | data
            name = BUTTONS.get(code) # แปลงรหัสเป็นชื่อปุ่ม
            wait = 1 # รีเซ็ตสถานะ
            
            if name: # ถ้าเป็นปุ่ม L1 หรือ L2
                print(f"Pressed: {name}")
                
                if name == "L1":
                    # เพิ่มมุมทีละ 1 องศา 
                    current_angle = current_angle + 1
                
                elif name == "L2":
                    # ลดมุมทีละ 1 องศา
                    current_angle = current_angle - 1
                
                # --- ระบบป้องกัน (Clamping) ---
                #  ล็อกค่าไว้ไม่ให้เกิน 0-180 
                if current_angle > 180: current_angle = 180
                if current_angle < 0:   current_angle = 0
                
                # --- ส่งคำสั่งไปที่เซอร์โว ---
                # อัปเดตตำแหน่งเซอร์โวตามค่ามุมใหม่ที่คำนวณได้
                set_servo(sv1, current_angle)
                print(f"Angle: {current_angle}")
