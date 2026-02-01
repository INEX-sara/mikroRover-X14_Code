from machine import Pin, PWM  # นำเข้าไลบรารีควบคุมขา Pin และสัญญาณ PWM
import time                   # นำเข้าไลบรารีจัดการเรื่องเวลา

M1_B = PWM(Pin(13)); M1_A = PWM(Pin(14)) # ล้อซ้าย ต่อขา 13, 14 
M2_B = PWM(Pin(16)); M2_A = PWM(Pin(17)) # ล้อขวา ต่อขา 16, 17 
M1_A.freq(1000); M1_B.freq(1000)         # ตั้งความถี่ 1000Hz
M2_A.freq(1000); M2_B.freq(1000)

start_button = Pin(8, Pin.IN, Pin.PULL_UP) # ปุ่ม SW1 สำหรับเริ่มทำงาน 
sensor_L = Pin(10, Pin.IN) # เซนเซอร์ด้านซ้าย ต่อขา 10 
sensor_R = Pin(11, Pin.IN) # เซนเซอร์ด้านขวา ต่อขา 11 

# ฟังก์ชันแปลงความเร็ว 0-100% เป็นค่า PWM 0-65535 
def _map_constrain(speed):
    if speed < 0: speed = 0
    if speed > 100: speed = 100
    return int(speed / 100 * 65535)

# --- ฟังก์ชันควบคุมทิศทาง ---
def fd(speed): # เดินหน้า 
    pwm = _map_constrain(speed)
    M1_A.duty_u16(pwm); M1_B.duty_u16(0)
    M2_A.duty_u16(pwm); M2_B.duty_u16(0)

def sl(speed): # หมุนซ้าย (Spin Left) เมื่อล้อซ้ายถอยหลัง ล้อขวาเดินหน้า
    pwm = _map_constrain(speed)
    M1_A.duty_u16(0); M1_B.duty_u16(pwm)
    M2_A.duty_u16(pwm); M2_B.duty_u16(0)

def sr(speed): # หมุนขวา (Spin Right) เมื่อล้อซ้ายเดินหน้า ล้อขวาถอยหลัง 
    pwm = _map_constrain(speed)
    M1_A.duty_u16(pwm); M1_B.duty_u16(0)
    M2_A.duty_u16(0); M2_B.duty_u16(pwm)

def ao(): # หยุดจ่ายไฟมอเตอร์ทั้งหมด (All Off)
    M1_A.duty_u16(0); M1_B.duty_u16(0)
    M2_A.duty_u16(0); M2_B.duty_u16(0)

# วนลูปรอจนกว่าจะกดปุ่ม SW1 ถึงจะเริ่มทำงาน 
while start_button.value() == 1:
    time.sleep_ms(10)

# --- ลูปหลักการเดินตามเส้น (Line Tracking Logic) ---
while True:
    left_val = sensor_L.value()  # อ่านค่าเซนเซอร์ซ้าย (1=ขาว, 0=ดำ) 
    right_val = sensor_R.value() # อ่านค่าเซนเซอร์ขวา (1=ขาว, 0=ดำ) 
    
    # 1. ถ้าทั้งสองตัวตรวจพบพื้นสีขาว ให้เดินหน้าต่อไป 
    if left_val == 1 and right_val == 1:
        fd(60)
    
    # 2. ถ้าเซนเซอร์ซ้ายเจอเส้นดำ ให้หมุนซ้ายเพื่อกลับเข้าหาเส้น 
    elif left_val == 0 and right_val == 1:
        sl(70)
    
    # 3. ถ้าเซนเซอร์ขวาเจอเส้นดำ ให้หมุนขวาเพื่อกลับเข้าหาเส้น
    elif left_val == 1 and right_val == 0:
        sr(70)
    
    # 4. ถ้าเจอเส้นดำทั้งคู่ (ทางแยกหรือเส้นตัด) ให้หยุด
    else:
        ao()
