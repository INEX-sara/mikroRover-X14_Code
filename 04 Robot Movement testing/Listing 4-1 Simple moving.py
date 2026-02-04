from machine import Pin, PWM  # นำเข้าไลบรารีควบคุมขา Pin และสัญญาณ PWM 
import time                   # นำเข้าไลบรารีจัดการเรื่องเวลา

# --- ตั้งค่าการควบคุมมอเตอร์ (Motor Setup) ---
# มอเตอร์ 1 (ซ้าย) ต่อกับขา 13 และ 14
M1_B = PWM(Pin(13))
M1_A = PWM(Pin(14))

# มอเตอร์ 2 (ขวา) ต่อกับขา 16 และ 17 
M2_B = PWM(Pin(16))
M2_A = PWM(Pin(17))

# กำหนดความถี่สัญญาณ PWM ที่ 1000Hz เพื่อให้มอเตอร์ทำงานได้เรียบ 
M1_A.freq(1000); M1_B.freq(1000)
M2_A.freq(1000); M2_B.freq(1000)

# --- ตั้งค่าปุ่มกด (Input Setup) ---
# กำหนด SW1 (ขา 8) และ SW2 (ขา 9) เป็นอินพุตแบบ Pull-up
sw1 = Pin(8, Pin.IN, Pin.PULL_UP)
sw2 = Pin(9, Pin.IN, Pin.PULL_UP)

# --- คำนวณความเร็ว (Speed Calculation) ---
speed_percent = 40  # กำหนดความเร็วที่ 40% 
# แปลงค่าเปอร์เซ็นต์เป็นค่า Duty Cycle (0-65535) 
pwm_duty = int(speed_percent / 100 * 65535)

while True:
    # อ่านค่าสถานะปุ่ม 
    sw1_pressed = (sw1.value() == 0)
    sw2_pressed = (sw2.value() == 0)

    # เงื่อนไข: ถ้ากดปุ่ม SW1 เพียงปุ่มเดียว (เดินหน้า) 
    if sw1_pressed and not sw2_pressed:
        # สั่งมอเตอร์ทั้งสองล้อหมุนไปทิศทางเดียวกัน (A=ความเร็ว, B=0) 
        M1_A.duty_u16(pwm_duty); M1_B.duty_u16(0)
        M2_A.duty_u16(pwm_duty); M2_B.duty_u16(0)
        time.sleep(1) # ทำงานค้างไว้ 1 วินาที 

    # เงื่อนไข: ถ้ากดปุ่ม SW2 เพียงปุ่มเดียว (ถอยหลัง) 
    elif not sw1_pressed and sw2_pressed:
        # สั่งมอเตอร์หมุนกลับทิศทาง (A=0, B=ความเร็ว) 
        M1_A.duty_u16(0); M1_B.duty_u16(pwm_duty)
        M2_A.duty_u16(0); M2_B.duty_u16(pwm_duty)
        time.sleep(1) # ทำงานค้างไว้ 1 วินาที 

    # กรณีไม่ได้กดปุ่มใดๆ ให้หยุดจ่ายไฟแก่มอเตอร์ทั้งหมด 
    M1_A.duty_u16(0); M1_B.duty_u16(0)
    M2_A.duty_u16(0); M2_B.duty_u16(0)
    
    time.sleep_ms(10)
