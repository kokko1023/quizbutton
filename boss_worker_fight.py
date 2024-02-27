from machine import Pin, PWM, UART
import time, utime

red = 2
pink = 6
servo = 10
boss = 14
btn_boss_correct = 15

high = 1
low = 0

# init
red_pin = machine.Pin(red, machine.Pin.IN)
boss_pin = machine.Pin(boss, machine.Pin.IN)
pink_pin = machine.Pin(pink, machine.Pin.OUT)
btn_boss_correct_pin = machine.Pin(btn_boss_correct, machine.Pin.IN)
servo_pwm = PWM(Pin(servo))
servo_pwm.freq(50)
# UART初期設定（UART番号,クロックレート,TXピン：GP4　RXピン：GP5）
uart = machine.UART(1,baudrate=9600,tx = machine.Pin(4),rx = machine.Pin(5))


def set_angle(angle):
    assert 20 <= angle <= 90, 'invalid angle'
    max_duty = 65025
    duty = int(max_duty * (((0.12 - 0.0725) / 90) * angle + 0.0725))
    servo_pwm.duty_u16(duty)
    
def calc_checksum(sum_data):
    temp = ~sum_data + 1 # 2の補数の計算(ビットを反転させて1を足す)
    h_byte = (temp & 0xFF00) >> 8
    l_byte = temp & 0x00FF
    return h_byte, l_byte

def send_data(command, param):
    ver      = 0xFF
    d_len    = 0x06
    feedback = 0x00
    param1  = (param & 0xFF00) >> 8
    param2  = param & 0x00FF
    cs1, cs2 = calc_checksum(ver + d_len + command + feedback + param1 + param2)
    sdata = bytearray([0x7E, ver, d_len, command, feedback, param1, param2, cs1, cs2, 0xEF])
    uart.write(sdata)

def init_sd():
    send_data(0x3F, 0x02) # 0x02でSDカードのみ有効化
    utime.sleep_ms(1000)

def set_volume(volume):
    send_data(0x06, volume)
    utime.sleep_ms(500)

def play_sound(num):
    # "mp3"という名称のフォルダ内に保存された、"0001.mp3"のような名称のファイルを再生
    print("Play {}".format(num))
    send_data(0x12, num)
    
def boss_correct(pin):
    init_sd()
    print("mp3")
    set_volume(15)
    num = 1
    play_sound(num)
    time.sleep(0.5)

btn_boss_correct_pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=boss_correct)

init_sd()
print("boot!")
set_volume(15)
num = 1
play_sound(num)

set_angle(90)

# polling
while True:
    if boss_pin.value() == high:
        print("boss push during polling")
    
    if red_pin.value() == high:
        print("worker push")
        
        # Polling for boss push within 7 seconds
        start_time = time.ticks_ms()
        angle = 90
        while (t := time.ticks_diff(time.ticks_ms(), start_time)) < 7000:
            if t % 700 == 0:
                set_angle(angle - 3)
            if boss_pin.value() == high:
                print("boss push as interrupting worker")
                set_angle(90)
                time.sleep(0.5)
                break
        
        else:
            print("worker ans")
            pink_pin.on()
            set_angle(20)
            time.sleep(0.3)
            pink_pin.off()
            time.sleep(2.0)
            set_angle(90)

