from machine import Pin, PWM, I2C, ADC 
from ssd1306 import SSD1306_I2C       
import time                         

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
display = SSD1306_I2C(128, 64, i2c, addr=0x3C)

# --- ตั้งค่ามอเตอร์ (Motor Setup) ---
M1_B = PWM(Pin(13)); M1_A = PWM(Pin(14)) # มอเตอร์ 1 (ซ้าย)
M2_B = PWM(Pin(16)); M2_A = PWM(Pin(17)) # มอเตอร์ 2 (ขวา)
M1_A.freq(1000); M1_B.freq(1000)         # ตั้งความถี่ 1000Hz
M2_A.freq(1000); M2_B.freq(1000)

# --- ตั้งค่าปุ่มกดและเซนเซอร์ ---
start_button = Pin(8, Pin.IN, Pin.PULL_UP) # ปุ่ม SW1 (ขา 8)
adc_sensor = ADC(Pin(27))                 # เซนเซอร์ ZX-SONAR1M (ขา 27)

# ฟังก์ชันคำนวณเปอร์เซ็นต์ความเร็ว (0-100) เป็นค่า Duty Cycle (0-65535)
def _map_constrain(speed):
    if speed < 0: speed = 0
    if speed > 100: speed = 100
    return int(speed / 100 * 65535)

# ฟังก์ชันเดินหน้า (Forward)
def fd(speed):
    pwm = _map_constrain(speed)
    M1_A.duty_u16(pwm); M1_B.duty_u16(0)
    M2_A.duty_u16(pwm); M2_B.duty_u16(0)

# ฟังก์ชันหยุดมอเตอร์ทั้งหมด (All Off)
def ao():
    M1_A.duty_u16(0); M1_B.duty_u16(0)
    M2_A.duty_u16(0); M2_B.duty_u16(0)

# --- เริ่มการทำงาน (Startup) ---
display.fill(0)
display.text("Press SW1", 0, 10, 1)      # แสดงข้อความรอให้กดปุ่ม
display.text("to Start...", 0, 25, 1)
display.show()

# วนลูปรอจนกว่าจะกดปุ่ม SW1
while start_button.value() == 1:
    time.sleep_ms(10)

speed = 50
fd(speed) # สั่งให้หุ่นยนต์เริ่มเดินหน้าด้วยความเร็ว 50%

while True:
    # อ่านค่าเซนเซอร์และคำนวณระยะทาง (cm)
    raw_value_16bit = adc_sensor.read_u16()
    distance = raw_value_16bit // 640  # คำนวณเป็นหน่วยเซนติเมตรโดยประมาณ 
    
    # แสดงสถานะและระยะทางบนหน้าจอ OLED
    display.fill(0)
    display.text("Moving Forward", 0, 10, 1)
    display.text("Dist: " + str(distance) + " cm", 0, 25, 1)
    display.show()
    
    # เงื่อนไขการตรวจสอบสิ่งกีดขวาง
    if distance < 10:  # ถ้าพบสิ่งกีดขวางใกล้กว่า 10 ซม.
        ao()           # สั่งให้หุ่นยนต์หยุดทันที 
        display.fill(0)
        display.text("Obstacle!", 0, 10, 1)
        display.text("STOPPED", 0, 25, 1)
        display.show()
        break          # ออกจากลูปการทำงาน
        
    time.sleep_ms(20) 
