from machine import Pin, PWM
import time

M1_B = PWM(Pin(13)); M1_A = PWM(Pin(14)) # มอเตอร์ล้อซ้าย
M2_B = PWM(Pin(16)); M2_A = PWM(Pin(17)) # มอเตอร์ล้อขวา
M1_A.freq(1000); M1_B.freq(1000)         # ตั้งความถี่ 1000Hz
M2_A.freq(1000); M2_B.freq(1000)

# --- ตั้งค่าเซอร์โวมอเตอร์ (Servo Setup) ---
sv_1 = PWM(Pin(18)) # เซอร์โวตัวยกแขน (ขา 18)
sv_2 = PWM(Pin(19)) # เซอร์โวตัวคีบ (ขา 19)
sv_1.freq(50); sv_2.freq(50)

sw1 = Pin(8, Pin.IN, Pin.PULL_UP)  # ปุ่มเริ่มงาน SW1
sw2 = Pin(9, Pin.IN, Pin.PULL_UP)  # ปุ่มสำรอง SW2
sensor_L = Pin(10, Pin.IN)         # เซนเซอร์เส้นด้านซ้าย
sensor_R = Pin(11, Pin.IN)         # เซนเซอร์เส้นด้านขวา

# --- กำหนดค่าคงที่สำหรับองศาเซอร์โว * ตำแหน่งอาจต่างกัน หาค่าที่เหมาะสมได้จาก Listing 7-1, 7-2 *---
sv1Up = 5      # ยกแขนขึ้น
sv1Down = 90   # วางแขนลง
sv2Pick = 100  # หุบคีบ
sv2Drop = 30   # กางออก

# --- ฟังก์ชันช่วยการทำงาน (Utility Functions) ---
def _map_constrain(speed): # จำกัดความเร็ว 0-100 และแปลงเป็น PWM
    if speed < 0: speed = 0
    if speed > 100: speed = 100
    return int(speed / 100 * 65535)

def map_value(x, in_min, in_max, out_min, out_max): # เทียบเคียงค่าองศา
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

def set_servo_angle(servo_pwm, angle): # สั่งงานเซอร์โวตามองศา
    if angle < 0: angle = 0
    if angle > 180: angle = 180
    duty_ns = map_value(angle, 0, 180, 500000, 2500000)
    servo_pwm.duty_ns(int(duty_ns))

# --- ฟังก์ชันควบคุมทิศทาง (Movement Functions) ---
def fd(speed): # เดินหน้า
    pwm = _map_constrain(speed)
    M1_A.duty_u16(pwm); M1_B.duty_u16(0)
    M2_A.duty_u16(pwm); M2_B.duty_u16(0)

def bk(speed): # ถอยหลัง
    pwm = _map_constrain(speed)
    M1_A.duty_u16(0); M1_B.duty_u16(pwm)
    M2_A.duty_u16(0); M2_B.duty_u16(pwm)

def sl(speed): # หมุนซ้าย
    pwm = _map_constrain(speed)
    M1_A.duty_u16(0); M1_B.duty_u16(pwm)
    M2_A.duty_u16(pwm); M2_B.duty_u16(0)

def sr(speed): # หมุนขวา
    pwm = _map_constrain(speed)
    M1_A.duty_u16(pwm); M1_B.duty_u16(0)
    M2_A.duty_u16(0); M2_B.duty_u16(pwm)

def ao(): # หยุดมอเตอร์ทั้งหมด
    M1_A.duty_u16(0); M1_B.duty_u16(0)
    M2_A.duty_u16(0); M2_B.duty_u16(0)

# --- ฟังก์ชันจัดการมือจับ (Gripper Functions) ---
def servoSet(): # ท่าเริ่มต้น
    set_servo_angle(sv_1, sv1Up)
    time.sleep_ms(500)
    set_servo_angle(sv_2, sv2Drop)
    time.sleep_ms(500)

def PickUp(): # ขั้นตอนคีบยก
    set_servo_angle(sv_1, sv1Down)
    time.sleep_ms(500)
    set_servo_angle(sv_2, sv2Pick)
    time.sleep_ms(500)
    set_servo_angle(sv_1, sv1Up)
    time.sleep_ms(500)

def DropDown(): # ขั้นตอนวางปล่อย
    set_servo_angle(sv_1, sv1Down)
    time.sleep_ms(1000)
    set_servo_angle(sv_2, sv2Drop)
    time.sleep_ms(500)
    set_servo_angle(sv_1, sv1Up)
    time.sleep_ms(500)

# --- ฟังก์ชันเดินตามเส้น (Line Tracking) ---
def track(): # เดินตามเส้นจนกว่าจะเจอเส้นตัด (ดำทั้งคู่)
    while True:
        left_val = sensor_L.value()
        right_val = sensor_R.value()
        if left_val == 1 and right_val == 1:
            fd(40)
        elif left_val == 0 and right_val == 1:
            sl(50)
        elif left_val == 1 and right_val == 0:
            sr(50)
        elif left_val == 0 and right_val == 0: # เจอเส้นตัด
            ao()
            break

# --- ส่วนการทำงานหลัก (Main Mission Logic) ---
while sw1.value() == 1: # รอกดปุ่มเริ่มงาน
    time.sleep_ms(10)

servoSet()      # ตั้งท่าเริ่มต้น
time.sleep(0.5)
track()         # 1. เดินตามเส้นไปจนถึงทางแยก/จุดคีบ

fd(50); time.sleep_ms(150); ao() # ขยับหน้าเล็กน้อยให้พ้นจุดตัด
while sensor_L.value() == 1:     # หมุนซ้ายหาเส้นถัดไป
    sl(40); time.sleep_ms(10)
ao()

track() # 2. เดินตามเส้นต่อ
ao(); time.sleep_ms(200)
PickUp() # 3. คีบวัตถุ

sl(40); time.sleep_ms(500)   # หมุนตัวกลับ
while sensor_L.value() == 1: # หาเส้นเพื่อเดินกลับ
    sl(40); time.sleep_ms(10)
ao()

track() # 4. เดินตามเส้นกลับ
fd(50); time.sleep_ms(150)
sr(40); time.sleep_ms(500)   # เลี้ยวขวาเข้าจุดวาง
while sensor_R.value() == 1:
    sr(40); time.sleep_ms(10)
ao()

track() # 5. เดินเข้าจุดวางสุดท้าย
ao(); time.sleep_ms(200)
DropDown() # 6. วางวัตถุจบภารกิจ
