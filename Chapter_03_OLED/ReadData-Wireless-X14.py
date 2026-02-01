from machine import Pin
import rp2
import time
# ---Configuration---
UART_PIN_ID = 12       # Use Port D3 (Pin 12)
BAUD_RATE   = 9600     # Wireless-X14 communication speed
TIMEOUT_MS  = 150      # Time limit to detect button release (milliseconds)
# Button Mapping Dictionary (Hex Code -> Button Name)
BUTTONS = {
    0x0011: "LU", 0x0021: "LL", 0x0081: "LD", 0x0041: "LR",
    0x1001: "RU", 0x4001: "RL", 0x8001: "RD", 0x2001: "RR",
    0x0009: "L1", 0x0005: "L2", 0x0003: "LT",
    0x0801: "R1", 0x0401: "R2", 0x0201: "RT"
}
# ---Create Signal Reader (PIO Setup)---
# This section uses Assembly language to create a custom UART reader
@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, autopush=True, push_thresh=8)
def uart_rx():
    wait(0, pin, 0)         # Wait for Start Bit (Logic 0)
    set(x, 7)       [10]    # Prepare loop for 8 bits
    label("bit_loop")       # Start of the loop
    in_(pins, 1)            # Read 1 bit of data
    nop()           [5]     # Wait for the next timing cycle
    jmp(x_dec, "bit_loop")  # Jump back to start of loop

# Initialize Pin and Start the State Machine
# Important: PULL_UP is enabled to prevent signal noise
pin_setup = Pin(UART_PIN_ID, Pin.IN, Pin.PULL_UP)
sm = rp2.StateMachine(0, uart_rx, freq=8*BAUD_RATE, in_base=pin_setup)
sm.active(1)
print(f"System Ready on Port D3 (Pin {UART_PIN_ID})...")
# ---Variables---
first_byte = 0              # Storage for the first part of data
waiting_for_byte1 = True    # State: Are we waiting for the first byte?
is_pressed = False          # State: Is a button currently being pressed?
last_time = time.ticks_ms() # Timestamp of the last received data
# ---Main Loop---
while True:
    current_time = time.ticks_ms()
    # --- Check for Button Release (Timeout) ---
    # If a button was pressed but no new data has arrived for > 150ms
    if is_pressed and time.ticks_diff(current_time, last_time) > TIMEOUT_MS:
        print("-> RELEASED")
        is_pressed = False
    # --- Check for Incoming Data ---
    if sm.rx_fifo(): # If there is data in the queue
        # Read 1 byte of data (0-255)
        data = sm.get() & 0xFF
        last_time = current_time # Update timestamp
        if waiting_for_byte1:
            # Step 1: Store the first byte
            first_byte = data
            waiting_for_byte1 = False # Move to next step
        else:
            # Step 2: Combine first byte and second byte
            # Logic: Shift first byte to the left by 8 bits, then add second byte
            keycode = (first_byte << 8) | data
            # Convert hex code to button name
            button_name = BUTTONS.get(keycode, "Unknown")
            # Filter out ignored codes (0x0000, 0x0001)
            if keycode not in (0, 1):
                # Display Button Name and Hex Code
                print(f"Button: {button_name:<15} | Code: 0x{keycode:04X}")
                is_pressed = True # Mark as pressed
            waiting_for_byte1 = True # Reset to wait for the next packet
