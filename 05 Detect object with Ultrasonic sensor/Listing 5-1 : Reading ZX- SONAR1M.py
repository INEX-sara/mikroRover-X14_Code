from machine import Pin, I2C, ADC   # นำเข้าคำสั่งควบคุมขา, การเชื่อมต่อ I2C และตัวแปลงสัญญาณอนาล็อก (ADC) 
from ssd1306 import SSD1306_I2C    
import time                        

# ใช้แชนเนล I2C 0, ขา SDA คือ Pin 4, ขา SCL คือ Pin 5, ความเร็ว 400kHz 
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
# กำหนดขนาดหน้าจอ 128x64 พิกเซล และที่อยู่ I2C คือ 0x3C 
display = SSD1306_I2C(128, 64, i2c, addr=0x3C)

# --- ตั้งค่าเซนเซอร์ระยะทาง ZX-SONAR1M ---
# เชื่อมต่อกับขา Pin 27 (ซึ่งเป็นช่อง ADC แชนเนล 1 ของ RP2040) 
adc_sensor = ADC(Pin(27))

while True:
    # อ่านค่าแรงดันไฟฟ้าดิบจากเซนเซอร์ (0-65535)
    raw_value = adc_sensor.read_u16() 
    
    # แปลงค่าจาก 16-บิต ให้เป็น 10-บิต (0-1023) โดยการหารด้วย 64 
    value_10bit = raw_value / 64 
    
    # คำนวณเป็นระยะทางหน่วยเซนติเมตร (โดยประมาณคือค่า ADC หารด้วย 10) 
    distance = value_10bit / 10 
    display.fill(0)                               # ล้างหน้าจอเดิม 
    display.text("Dist (cm):", 0, 10, 1)          # พิมพ์ข้อความหัวข้อที่พิกัด x=0, y=10 
    display.text( str(int(distance)) , 0, 25, 1) # พิมพ์ตัวเลขระยะทาง (แปลงเป็นเลขเต็ม) ที่พิกัด x=0, y=25
    display.show()                                # สั่งให้จออัปเดตภาพเพื่อแสดงผล 
    time.sleep_ms(100) # หน่วงเวลา 0.1 วินาที 
