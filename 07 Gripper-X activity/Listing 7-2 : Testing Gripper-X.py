from machine import Pin, PWM, I2C   
from ssd1306 import SSD1306_I2C    
import time                        

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
display = SSD1306_I2C(128, 64, i2c, addr=0x3C)

# --- ตั้งค่าเซอร์โวมอเตอร์สำหรับมือจับ (Grip Servo) ---
SV2_PIN = 18               # ในโค้ดนี้กำหนดใช้ขา GPIO18 สำหรับควบคุมเซอร์โวตัวคีบ 
sv_pick = PWM(Pin(SV2_PIN)) # สร้างสัญญาณ PWM บนขาที่กำหนด [cite: 1847]
sv_pick.freq(50)           # ตั้งความถี่มาตรฐานสำหรับเซอร์โวมอเตอร์ที่ 50Hz 

sw1 = Pin(8, Pin.IN, Pin.PULL_UP) # ปุ่ม SW1 สำหรับลดค่าองศา 
sw2 = Pin(9, Pin.IN, Pin.PULL_UP) # ปุ่ม SW2 สำหรับเพิ่มค่าองศา

current_angle = 90 # เริ่มต้นตั้งตำแหน่งเซอร์โวไว้ที่ 90 องศา [cite: 1846]

# ฟังก์ชันเทียบเคียงค่า (Mapping) เพื่อแปลงองศาเป็นค่าความกว้างพัลส์หน่วยนาโนวินาที (ns)
def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

# ฟังก์ชันสั่งงานเซอร์โวมอเตอร์ตามเลของศาที่ระบุ
def set_servo_angle(servo_pwm, angle):
    if angle < 0: angle = 0      # ป้องกันไม่ให้องศาต่ำกว่า 0 
    if angle > 180: angle = 180  # ป้องกันไม่ให้องศาเกิน 180 
    # แปลงองศา 0-180 ให้เป็นพัลส์ช่วง 0.5ms (500,000ns) ถึง 2.5ms (2,500,000ns)
    duty_ns = map_value(angle, 0, 180, 500000, 2500000)
    servo_pwm.duty_ns(int(duty_ns)) # ส่งค่าพัลส์ในหน่วยนาโนวินาทีไปยังเซอร์โว 

# วนลูปรอจนกว่าจะมีการกดปุ่ม SW1 เพื่อเริ่มต้นการทดสอบ
while sw1.value() == 1:
    time.sleep_ms(10)

# เมื่อเริ่มโปรแกรม ให้สั่งเซอร์โวไปที่ตำแหน่งเริ่มต้น (90 องศา) 
set_servo_angle(sv_pick, current_angle)

while True:
    sw1_pressed = (sw1.value() == 0) # ตรวจสอบการกดปุ่ม SW1 (0 คือกด)
    sw2_pressed = (sw2.value() == 0) # ตรวจสอบการกดปุ่ม SW2 (0 คือกด) 
    
    # หากกด SW1 ให้ค่อยๆ ลดองศาลง 
    if sw1_pressed and not sw2_pressed and current_angle > 0:
        current_angle -= 1
    # หากกด SW2 ให้ค่อยๆ เพิ่มองศาขึ้น 
    elif not sw1_pressed and sw2_pressed and current_angle < 180:
        current_angle += 1
        
    set_servo_angle(sv_pick, current_angle) # อัปเดตองศาไปยังเซอร์โวมอเตอร์จริง 
    
    # แสดงค่าองศาปัจจุบันบนหน้าจอ OLED 
    display.fill(0)                                # ล้างจอแสดงผล 
    display.text("SV2 (GP19):", 0, 10, 1)          # แสดงข้อความระบุขาใช้งาน 
    display.text(str(current_angle), 0, 25, 1)     # แสดงค่าเลของศาปัจจุบัน 
    display.show()                                 # สั่งหน้าจอให้อัปเดตผล 
    
    time.sleep_ms(50) 
