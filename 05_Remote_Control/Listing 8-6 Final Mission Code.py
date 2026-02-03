from machine import Pin, PWM  # เรียกใช้ Pin (คุมไฟเข้า/ออก) และ PWM (คุมความเร็ว/องศา)
import rp2                    # เรียกใช้ rp2 เพื่อควบคุม PIO (ตัวรับสัญญาณความเร็วสูง)
import time                   # เรียกใช้ time เพื่อจับเวลา

# --- [ส่วนตั้งค่าคงที่] ---
UART_PIN   = 12    # กำหนดขา D3 (GPIO 12) เป็นขารับสัญญาณจากจอย
BAUD_RATE  = 9600  # ความเร็วในการส่งข้อมูลของจอย Wireless-X14
TIMEOUT_MS = 150   # ถ้าจอยเงียบเกิน 0.15 วินาที จะถือว่าปล่อยมือ (Safety)
SPEED      = 50    # ความเร็วในการวิ่งของหุ่นยนต์ (ค่า 0-100)

# --- มอเตอร์ขับเคลื่อน (DC Motors) ---
# กำหนดขาและสร้าง PWM สำหรับมอเตอร์ ความถี่ 1000Hz (เหมาะกับมอเตอร์ DC)
m1a = PWM(Pin(14)); m1a.freq(1000)  # ล้อซ้าย ขั้ว A
m1b = PWM(Pin(13)); m1b.freq(1000)  # ล้อซ้าย ขั้ว B
m2a = PWM(Pin(17)); m2a.freq(1000)  # ล้อขวา ขั้ว A
m2b = PWM(Pin(16)); m2b.freq(1000)  # ล้อขวา ขั้ว B

# --- เซอร์โวมอเตอร์ (Servo Motors) ---
# กำหนดขา PWM ความถี่ 50Hz (มาตรฐานของ Servo Motor)
sv1 = PWM(Pin(18)); sv1.freq(50) # Servo 1
sv2 = PWM(Pin(19)); sv2.freq(50) # Servo 2

# --- ฟังก์ชันย่อย ---
# ฟังก์ชันแปลงความเร็ว (0-100) เป็นค่า Duty Cycle (0-65535) 
def set_speed(pin, value):
    # สูตร: (ค่า/100) * 65535 แปลงเป็นเลขจำนวนเต็ม
    duty = int(max(0, min(100, value)) * 655.35)
    pin.duty_u16(duty) # สั่งจ่ายไฟตามความแรงที่คำนวณได้

# ฟังก์ชันสั่งหยุดรถ (ตัดไฟมอเตอร์ทุกตัว)
def stop():
    m1a.duty_u16(0); m1b.duty_u16(0)
    m2a.duty_u16(0); m2b.duty_u16(0)

# ฟังก์ชันเดินหน้า (Forward)
def fd(s): 
    # ล้อซ้ายหมุนไปข้างหน้า 
    set_speed(m1a, s); m1b.duty_u16(0) 
    # ล้อขวาหมุนไปข้างหน้า
    set_speed(m2a, s); m2b.duty_u16(0)

# ฟังก์ชันถอยหลัง (Backward)
def bk(s): 
    # สลับขั้วการจ่ายไฟ เพื่อให้ล้อหมุนกลับหลัง
    m1a.duty_u16(0); set_speed(m1b, s)
    m2a.duty_u16(0); set_speed(m2b, s)

# ฟังก์ชันหมุนซ้าย (Spin Left)
def sl(s): 
    # ล้อซ้ายถอยหลัง + ล้อขวาเดินหน้า = หมุนตัวทางซ้าย
    m1a.duty_u16(0); set_speed(m1b, s) 
    set_speed(m2a, s); m2b.duty_u16(0) 

# ฟังก์ชันหมุนขวา (Spin Right)
def sr(s): 
    # ล้อซ้ายเดินหน้า + ล้อขวาถอยหลัง = หมุนตัวทางขวา
    set_speed(m1a, s); m1b.duty_u16(0) 
    m2a.duty_u16(0); set_speed(m2b, s) 
   
# ฟังก์ชันควบคุมองศาเซอร์โว (0-180 องศา)
def set_servo(servo, angle):
    # สูตรแปลง 0-180 องศา เป็นหน่วย Nanoseconds (ns) สำหรับ Pulse Width
    # 500,000ns (0.5ms) = 0 องศา, 2,500,000ns (2.5ms) = 180 องศา
    duty = 500_000 + int(angle * 2_000_000 // 180)
    servo.duty_ns(duty)

# ตารางจับคู่รหัสปุ่ม (Hex Code) กับชื่อปุ่ม (ค่าของแต่ละปุ่มอาจแตกต่างกัน)
BUTTONS = {
    # ทิศทาง
    0x0011: "LU", 0x0081: "LD", 0x0021: "LL", 0x0041: "LR",
    # เซอร์โว
    0x0009: "L1", 0x0005: "L2", 
    0x0801: "R1", 0x0401: "R2"
}

# --- ส่วนของ PIO (Programmable I/O) ---
# เขียนภาษา Assembly จำลองการทำงานเป็นตัวรับ UART (Serial)
@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, autopush=True, push_thresh=8)
def uart_rx():
    wait(0, pin, 0)      # 1. รอจนกว่าจะมีสัญญาณเริ่ม (Start Bit)
    set(x, 7) [10]       # 2. ตั้งตัวนับ 8 บิต และรอให้ถึงกลางบิตแรก
    label("b")           # จุดวนลูป
    in_(pins, 1)         # 3. อ่านค่า 1 บิต
    nop() [5]            # 4. รอเวลาให้ตรงจังหวะความเร็ว (Baudrate)
    jmp(x_dec, "b")      # 5. วนกลับไปทำจนครบ 8 บิต

# สร้าง State Machine (SM) เพื่อรันโค้ด PIO ด้านบน
sm = rp2.StateMachine(0, uart_rx, freq=8*BAUD_RATE, in_base=Pin(UART_PIN, Pin.IN, Pin.PULL_UP))
sm.active(1) # สั่งให้เริ่มทำงาน

# ตัวแปรช่วยประมวลผลข้อมูล
b1 = 0                  # เก็บข้อมูลไบต์แรก
wait = 1                # สถานะ (1=รอไบต์แรก, 0=ได้ไบต์แรกแล้วรอไบต์สอง)
press = 0               # สถานะการกด (0=ปล่อย, 1=กด)
last = time.ticks_ms()  # เวลาล่าสุดที่ได้รับข้อมูล

# ตั้งค่ามุมเริ่มต้นของ Servo
angle1 = 90
angle2 = 90
set_servo(sv1, angle1)
set_servo(sv2, angle2)

# --- ลูปหลัก (ทำงานตลอดเวลา) ---
while True:
    now = time.ticks_ms() # ดูเวลาปัจจุบัน
    
    # [ระบบ Safety] ถ้ามีการกดค้างไว้ แต่ไม่มีข้อมูลใหม่เกิน 0.15 วิ แสดงว่าสัญญาณหลุด/ปล่อยมือ
    if press and time.ticks_diff(now, last) > TIMEOUT_MS:
        stop()            # สั่งหยุดรถทันที
        print("-> หยุด (ปล่อยมือ)")
        press = 0         # รีเซ็ตสถานะ

    # ตรวจสอบว่ามีข้อมูลส่งมาจาก PIO หรือไม่
    if sm.rx_fifo():
        data = sm.get() & 0xFF # อ่านข้อมูลออกมา 1 ไบต์
        last = now             # อัปเดตเวลาล่าสุด (เพื่อไม่ให้ Safety ทำงาน)
        
        if wait: 
            b1 = data; wait = 0 # ถ้าเป็นไบต์แรก ให้เก็บไว้ก่อน
        else:
            # ถ้าเป็นไบต์ที่สอง ให้นำมารวมกับไบต์แรก (Shift & OR)
            code = (b1 << 8) | data 
            name = BUTTONS.get(code) # แปลงรหัสเป็นชื่อปุ่ม
            wait = 1 # เตรียมรอรับชุดถัดไป
            
            if name: # ถ้าเป็นปุ่มที่เรารู้จัก
                press = 1    
                # --- ส่วนควบคุมการขับเคลื่อน ---
                if   name == "LU": fd(SPEED)  # เดินหน้า
                elif name == "LD": bk(SPEED)  # ถอยหลัง
                elif name == "LL": sl(SPEED)  # หมุนซ้าย
                elif name == "LR": sr(SPEED)  # หมุนขวา
                
                # --- ส่วนควบคุมแขนจับ (Servo 1) ---
                elif name == "L1":
                    angle1 = min(180, angle1 + 1) # เพิ่มมุม (max 180)
                    set_servo(sv1, angle1)        # สั่งขยับ
                elif name == "L2":
                    angle1 = max(0, angle1 - 1)   # ลดมุม (min 0)
                    set_servo(sv1, angle1)
                
                # --- ส่วนควบคุมแขนจับ (Servo 2) ---
                elif name == "R1":
                    angle2 = min(180, angle2 + 1)
                    set_servo(sv2, angle2)
                elif name == "R2":
                    angle2 = max(0, angle2 - 1)
                    set_servo(sv2, angle2)
