from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

# ตั้งค่าการเชื่อมต่อ I2C (เลือก Channel, ขา SDA, ขา SCL และความเร็ว)
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

# เริ่มต้นใช้งานจอ OLED (กว้าง 128, สูง 64, อ้างอิง i2c, Address ของจอ)
display = SSD1306_I2C(128, 64, i2c, addr=0x3C)

# ล้างหน้าจอให้เป็นสีดำทั้งหมด
display.fill(0)

# เขียนข้อความ (ข้อความ, พิกัด X, พิกัด Y, สี)
display.text("Hello, world!", 0, 10, 1)

# สั่งให้หน้าจอแสดงผลข้อมูลที่เขียนไว้
display.show()
