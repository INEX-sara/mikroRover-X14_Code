from machine import Pin, PWM
import rp2
import time

UART_PIN   = 12    # ขา D3
BAUD_RATE  = 9600
TIMEOUT_MS = 150   # เวลาเช็คปล่อยมือ
SPEED      = 60    # ความเร็ว (0-100)

m1a = PWM(Pin(13)); m1a.freq(1000) 
m1b = PWM(Pin(14)); m1b.freq(1000)
m2a = PWM(Pin(16)); m2a.freq(1000)
m2b = PWM(Pin(17)); m2b.freq(1000)

def set_speed(pin, value):
    duty = int(max(0, min(100, value)) * 655.35)
    pin.duty_u16(duty)

def stop():
    m1a.duty_u16(0); m1b.duty_u16(0)
    m2a.duty_u16(0); m2b.duty_u16(0)

def forward(s):
    m1a.duty_u16(0); set_speed(m1b, s) 
    m2a.duty_u16(0); set_speed(m2b, s)

def backward(s):
    set_speed(m1a, s); m1b.duty_u16(0)
    set_speed(m2a, s); m2b.duty_u16(0)

def turn_left(s):
    set_speed(m1a, s); m1b.duty_u16(0) 
    m2a.duty_u16(0); set_speed(m2b, s) 

def turn_right(s):
    m1a.duty_u16(0); set_speed(m1b, s) 
    set_speed(m2a, s); m2b.duty_u16(0) 

BUTTONS = {
    0x0011: "LU", 
    0x0081: "LD",  
    0x0021: "LL",  
    0x0041: "LR"   
}

@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, autopush=True, push_thresh=8)
def uart_rx():
    wait(0, pin, 0); set(x, 7) [10]; label("b")
    in_(pins, 1); nop() [5]; jmp(x_dec, "b")

sm = rp2.StateMachine(0, uart_rx, freq=8*BAUD_RATE, in_base=Pin(UART_PIN, Pin.IN, Pin.PULL_UP))
sm.active(1)
print("Ready! Full Control (FW/BK/LT/RT)")

b1, wait, press, last = 0, 1, 0, time.ticks_ms()

while True:
    now = time.ticks_ms()

    if press and time.ticks_diff(now, last) > TIMEOUT_MS:
        stop()
        press = 0

    if sm.rx_fifo():
        data = sm.get() & 0xFF; last = now
        
        if wait: 
            b1 = data; wait = 0
        else:
            code = (b1 << 8) | data
            name = BUTTONS.get(code, "Unknown")
            wait = 1
            
            if name != "Unknown":
                press = 1

                if   name == "LU": forward(SPEED)    
                elif name == "LD": backward(SPEED)   
                elif name == "LL": turn_left(SPEED)  
                elif name == "LR": turn_right(SPEED) 
