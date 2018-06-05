from Tkinter import *
from random import randint
import ctypes
import time
import pyfirmata
from PIL import Image
import cv2
import zbar

""""
Program Requisites:
    -Running on Python 2.7.15
    -Run from the CMD (requisite from zbar)
    -Connect to Arduino (Mega2560 preferably)
    -Have all environment packages imported above (I recommend using Anaconda
    -Connect to Epson C3 Robotic Arm, running Blackjack program

Brief Description:
    This program runs in conjunction with the EpsonRC+ 5.0 software to play Blackjack with the
    robotic arm. It contains the game logic, Blackjack GUI and digital communication in both directions with the arm
    using Arduino interfacing.
    -ERV
"""

### Classes ### (Used like variable bins in this program)


class account:
    balance = 500
    bet = 0

class armstat:
    ino_setup = False  # Set this to False when connected to Mega 2560

class gamestat:
    first = 1
    prevbet = 0
    phand = []
    dhand = []


## FUNCTIONS ###


def qrscan(player):
    """
    A simple function that captures webcam video utilizing OpenCV. The video is then broken down into frames which
    are constantly displayed. The frame is then converted to grayscale for better contrast. Afterwards, the image
    is transformed into a numpy array using PIL. This is needed to create zbar image. This zbar image is then scanned
    utilizing zbar's image scanner and will then print the decodeed message of any QR or bar code. To quit the program,
    press "q".
    :return:
    https://github.com/allenywang/Real-Time-QR-Recognizer-Reader-and-Decoder/blob/master/RTQR.py
    """
    # Begin capturing video. You can modify what video source to use with VideoCapture's argument. It's currently set
    # to be your webcam.
    capture = cv2.VideoCapture(1) # Set to 0 if using integrated webcam and 1 for USB external webcam
    detected = 0
    while not detected:
        # To quit this program press q.
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Breaks down the video into frames
        ret, frame = capture.read()

        # Displays the current frame
        cv2.imshow('Current', frame)

        # Converts image to grayscale.
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Uses PIL to convert the grayscale image into a ndary array that ZBar can understand.
        image = Image.fromarray(gray)
        width, height = image.size
        zbar_image = zbar.Image(width, height, 'Y800', image.tostring())

        # Scans the zbar image.
        scanner = zbar.ImageScanner()
        scanner.scan(zbar_image)

        # Prints data from image.

        for decoded in zbar_image:  # Modified for Blackjack Code
            detected = 1
            if not player:
                print_log("Card added to dealer...")
                gamestat.dhand.append(int(decoded.data))
            else:
                print_log("Card added to player...")
                gamestat.phand.append(int(decoded.data))
            refresh_score()
            window.update()
            cv2.destroyWindow('Current')


def wait_arm():
    while busy.read():
        time.sleep(1)


def arm_routine(routine):
    if routine < 8:
        ledlist = []
        binum = bin(routine)
        for item in range(len(binum) - 1, 0, -1):
            if binum[item] != "b":
                ledlist.insert(0, int(binum[item]))
        if len(binum) - 2 < 3:
            for item in range(0, 3 - (len(binum) - 2), 1):
                ledlist.insert(0, 0)

        led1.write(ledlist[0])  # MSB
        led2.write(ledlist[1])
        led3.write(ledlist[2])  # LSB
        if not virtual.get():
            wait_arm()
            time.sleep(2)
        else:
            pass
    else:
        print_log("Routine does not exist")


def reset_buttons():  # Resets button after one round (Repeat, Deal, Bets)
    print_log("Reset buttons")
    repeat_button.config(state=ACTIVE)
    deal_button.config(state=ACTIVE)
    hit_button.config(state=DISABLED)
    stand_button.config(state=DISABLED)
    dd_button.config(state=DISABLED)
    chip25_button.config(state=ACTIVE)
    chip50_button.config(state=ACTIVE)
    chip100_button.config(state=ACTIVE)
    mchip25_button.config(state=ACTIVE)
    mchip50_button.config(state=ACTIVE)
    mchip100_button.config(state=ACTIVE)
    window.update()


def playing_buttons():  # Sets button Hit and Stand
    print_log("Playing buttons")
    repeat_button.config(state=DISABLED)
    deal_button.config(state=DISABLED)
    hit_button.config(state=ACTIVE)
    stand_button.config(state=ACTIVE)
    dd_button.config(state=DISABLED)
    chip25_button.config(state=DISABLED)
    chip50_button.config(state=DISABLED)
    chip100_button.config(state=DISABLED)
    mchip25_button.config(state=DISABLED)
    mchip50_button.config(state=DISABLED)
    mchip100_button.config(state=DISABLED)
    window.update()


def dd_buttons():  # Sets button Hit , Double Down and Stand
    print_log("Playing buttons")
    repeat_button.config(state=DISABLED)
    deal_button.config(state=DISABLED)
    hit_button.config(state=ACTIVE)
    stand_button.config(state=ACTIVE)
    dd_button.config(state=ACTIVE)
    chip25_button.config(state=DISABLED)
    chip50_button.config(state=DISABLED)
    chip100_button.config(state=DISABLED)
    mchip25_button.config(state=DISABLED)
    mchip50_button.config(state=DISABLED)
    mchip100_button.config(state=DISABLED)
    window.update()


def disable_buttons():
    print_log("Disabled buttons")
    repeat_button.config(state=DISABLED)
    deal_button.config(state=DISABLED)
    hit_button.config(state=DISABLED)
    stand_button.config(state=DISABLED)
    dd_button.config(state=DISABLED)
    chip25_button.config(state=DISABLED)
    chip50_button.config(state=DISABLED)
    chip100_button.config(state=DISABLED)
    mchip25_button.config(state=DISABLED)
    mchip50_button.config(state=DISABLED)
    mchip100_button.config(state=DISABLED)
    window.update()


def deal_flag(hand):
    flag = 0
    for card in hand:
        if card == 1 or card == 10:
            flag = 1
    return flag


def refresh_accounts():
    print_bet.config(text="Bet: " + str(account.bet))
    print_balance.config(text="Balance: " + str(account.balance))
    window.update()


def bet(number):
    if number > 0 and (account.balance - number) < 0:
        print_log("Balance not available...")
    elif number < 0 and (account.bet + number) < 0:
        print_log("Cannot take this action...")
    else:
        account.bet += number
        account.balance -= number
        refresh_accounts()
        print_log("Player managed chips...")


def refresh_score():
    pscorelbl.config(text=str(hand_total(gamestat.phand)))
    dscorelbl.config(text=str(hand_total(gamestat.dhand)))


def arm_dhit(vir):
    if not vir.get():
        print_log("Arm D_Hit")
        window.update()
        arm_routine(1)
        qrscan(0)
        arm_routine(2)
        arm_routine(0)
    else:
        print_log("Arm to Scan Card")
        gamestat.dhand.append(randint(1, 10))
        print_log("Card Scanned")
        print_log("Arm to dealer")
        print_log("Virtual Arm Ready")


def arm_phit(vir):
    if not vir.get():
        print_log("Arm P_Hit")
        window.update()
        arm_routine(1)
        qrscan(1)
        arm_routine(3)
        arm_routine(0)
    else:
        print_log("Arm to Scan Card")
        gamestat.phand.append(randint(1, 10))
        print_log("Card Scanned")
        print_log("Arm to player")
        print_log("Virtual Arm Ready")


def dealfx():
    print_log("DealFX")
    gamestat.phand = []
    gamestat.dhand = []
    refresh_score()
    window.update()
    if account.bet:
        print_log("Bet placed sucesfully")
        gamestat.first = 1
        gamestat.prevbet = account.bet
        arm_phit(virtual)
        arm_dhit(virtual)
        arm_phit(virtual)
        if hand_total(gamestat.phand) == 21 and not deal_flag(gamestat.dhand):
            print_log("Blackjack Win!")
            account.balance += 0.5 * account.bet
            dhitfx()
            player_wins()
            window.update()
        elif hand_total(gamestat.phand) == 21 and deal_flag(gamestat.dhand):
            print_log("Player has Blackjack!")
            print_log("Waiting for dealer")
            dhitfx()
            if hand_total(gamestat.dhand) == 21:
                print_log("Push!")
                push()
            else:
                print_log("Player Wins!")
                player_wins()
        else:
            dd_buttons()
    else:
        print_log("Player must place bet...")


def dhitfx():  # Placeholder function for GUI button
        print_log("Dealer hits")
        arm_dhit(virtual)


def phitfx():
    if gamestat.first:
        print_log("First hit")
        gamestat.first = 0
        playing_buttons()

    else:
        print_log("Player Hit")
    arm_phit(virtual)
    if hand_total(gamestat.phand) > 21:
        print_log("Player went over 21")
        arm_dhit(virtual)
        player_loses()


def ddfx():
    if (account.balance - account.bet) > 0:
        print_log("Player doubles down!")
        gamestat.first = 1
        account.balance -= account.bet
        account.bet *= 2
        disable_buttons()
        phitfx()
        standfx()
    else:
        print_log("Cannot double down...")


def standfx():
    print_log("Player stands")
    disable_buttons()
    while hand_total(gamestat.dhand) < 17 and hand_total(gamestat.dhand) <= hand_total(gamestat.phand):
        dhitfx()
        window.update()
    if hand_total(gamestat.dhand) > 21:
        print_log("Dealer over 21")
        player_wins()
    elif hand_total(gamestat.phand) > hand_total(gamestat.dhand):
        print_log("Player has more than dealer")
        player_wins()
    elif hand_total(gamestat.phand) == hand_total(gamestat.dhand):
        push()
    else:
        player_loses()
    reset_buttons()


def repeatbetfx():

    if account.bet != 0:
        print_log("Rebalanced accounts")
        account.balance += account.bet
        account.bet = 0
    if account.balance < gamestat.prevbet:
        print_log("Balance not available...")
    else:
        print_log("Repeat bet...")
        repeat_button.config(state=DISABLED)
        bet(gamestat.prevbet)
        refresh_accounts()
        window.update()
        dealfx()


def hand_total(hand):
    total = 0
    flag = 0
    for card in hand:
        total += card
        if card == 1:
            flag = 1
    if flag == 1 and (total + 10) <= 21:
        return total + 10
    else:
        return total


def print_log(strng):
    text_log.insert(INSERT, strng + "\n")


def player_wins():
    print_log("Player Wins!")
    account.balance += 2*account.bet
    account.bet = 0
    refresh_accounts()
    arm_routine(4)
    arm_routine(0)
    reset_buttons()


def player_loses():
    print_log("Dealer Wins!")
    account.bet = 0
    refresh_accounts()
    arm_routine(4)
    arm_routine(0)
    if not account.balance:
        account.balance = 25
    reset_buttons()

def push():
    print_log("Push!")
    account.balance += account.bet
    account.bet = 0
    refresh_accounts()
    arm_routine(4)
    arm_routine(0)
    reset_buttons()

## MAIN ###

if __name__ == "__main__":
    # Initialize Variables
    player_score = 0
    dealer_score = 0

    # Get computer resolution
    user32 = ctypes.windll.user32
    max_width = user32.GetSystemMetrics(0)
    max_height = user32.GetSystemMetrics(1)

    # GUI Code
    window = Tk()
    window.state("zoomed")
    window.title("UPRM Robotic Arm Blackjack")
    window.configure(background="#1D2731")

    virtual = IntVar()

    main_top = Frame(window, width=max_width, height=.1*max_height, bg="black")
    main_top.pack_propagate(0)
    main_top.pack(side=TOP)

    lbl_header = Label(main_top, font=('times', 32), bg = "black", fg="white", text="Robotic Arm Blackjack Project - GUI")
    lbl_header.place(relx=0.26, rely=.2)

    virtual_button = Checkbutton(main_top, relief=FLAT, padx=5, pady=5, bg="grey", text="Virtual Arm", fg="black", font=('times', 14), variable=virtual, justify=RIGHT)
    virtual_button.place(relx=0.85, rely=.2)

    main_left = Frame(window, width=.75*max_width, height=.9*max_height, bg="#F5F5F5")
    main_left.pack_propagate(0)
    main_left.pack(side=LEFT)

    main_right = Frame(window, width=.25*max_width, height=.9*max_height, bg="#F5F5F5")
    main_right.pack_propagate(0)
    main_right.pack(side=RIGHT)

    left_top = Frame(main_left, width=.75*max_width, height=.6*max_height, bg="#F5F5F5")
    left_top.pack_propagate(0)
    left_top.pack(side=TOP)

    chips_frame = LabelFrame(main_left, width=.75*max_width, height=.3*max_height, bg="#F5F5F5", text="Chip Management", font=('times', 16), labelanchor=N)
    chips_frame.pack_propagate(0)
    chips_frame.pack(side=LEFT)

    chip25_button = Button(chips_frame, padx=30, pady=20, font=('times', 16), text="25", bg="#303030", fg="white", justify=CENTER, relief=RAISED, bd=5, command = lambda: bet(25))
    chip25_button.place(x=110, y=20)

    chip50_button = Button(chips_frame, padx=30, pady=20, font=('times', 16), text="50", bg="#303030", fg="white", justify=CENTER, relief=RAISED, bd=5, command=lambda: bet(50))
    chip50_button.place(x=250, y=20)

    chip100_button = Button(chips_frame, padx=25, pady=20, font=('times', 16), text="100", bg="#303030", fg="white", justify=CENTER, relief=RAISED, bd=5, command=lambda: bet(100))
    chip100_button.place(x=390, y=20)

    mchip25_button = Button(chips_frame, padx=40, pady=0, font=('times', 12), text="-", bg="#303030", fg="white", justify=CENTER, relief=RAISED, bd=5, command=lambda: bet(-25))
    mchip25_button.place(x=110, y=110)

    mchip50_button = Button(chips_frame, padx=40, pady=0, font=('times', 12), text="-", bg="#303030", fg="white", justify=CENTER, relief=RAISED, bd=5, command=lambda: bet(-50))
    mchip50_button.place(x=250, y=110)

    mchip100_button = Button(chips_frame, padx=40, pady=0, font=('times', 12), text="-", bg="#303030", fg="white", justify=CENTER, relief=RAISED, bd=5, command=lambda: bet(-100))
    mchip100_button.place(x=390, y=110)

    print_balance = Label(chips_frame, font=('times', 18), bg="#303030", text="Balance: " + str(account.balance), fg="white", padx=40, pady=40)
    print_balance.place(x=600, y=20)

    print_bet = Label(chips_frame, font=('times', 18), bg="#303030", text="Bet: " + str(account.bet),fg="white", padx=80, pady=40)
    print_bet.place(x=850, y=20)

    score_frame = LabelFrame(left_top, width=.2*max_width, height=.6*max_height, bg="#F5F5F5", text="Live Scoring", font=('times', 16),labelanchor=N)
    score_frame.pack_propagate(0)
    score_frame.pack(side=LEFT)

    dealerlbl = Label(score_frame, font=('times', 18, 'bold'), bg="#F5F5F5", fg="black", text="Dealer Score", padx=5, pady=5)
    dealerlbl.place(relx=.22, rely=.10)

    playerlbl = Label(score_frame, font=('times', 18, 'bold'), bg="#F5F5F5", fg="black", text="Player Score", padx=5, pady=5)
    playerlbl.place(relx=.22, rely=.77)

    pscorelbl = Label(score_frame, font=('times', 18, 'bold'), bg="#F5F5F5", fg="black", text=str(hand_total(gamestat.phand)), padx=30, pady=15)
    pscorelbl.place(relx=.32, rely=.57)

    dscorelbl = Label(score_frame, font=('times', 18, 'bold'), bg="#F5F5F5", fg="black", text=dealer_score, padx=30, pady=15)
    dscorelbl.place(relx=.32, rely=.27)

    vslbl = Label(score_frame, font=('times', 13, 'bold'), bg="#F5F5F5", fg="black", text="VS", padx=28, pady=15)
    vslbl.place(relx=.32, rely=.43)

    player_frame = LabelFrame(left_top, width=.55*max_width, height=.6*max_height, bg="#303030", text="Player Options", font=('times', 16), fg="white", labelanchor=N)
    player_frame.pack_propagate(0)
    player_frame.pack(side=RIGHT)

    out_frame = LabelFrame(player_frame, width=.25*max_width, height=.1*max_height, font=('times', 10, 'bold'), labelanchor=S, bg="black", fg="white", text=" Display ")
    out_frame.pack_propagate(0)
    out_frame.place(relx=.28, rely=.05)

    out_text = Label(out_frame, font=('times', 14), bg="black", fg="white", text="Waiting for the player to place bet...", justify=CENTER, width= 40, height=1)
    out_text.pack(side=LEFT)

    hit_button = Button(player_frame, padx=120, pady=20, font=('times', 16), text="Hit", bg="#F5F5F5", relief=RIDGE, justify=CENTER, state=DISABLED, command=phitfx)
    hit_button.place(relx=.15, rely=.3)

    stand_button = Button(player_frame, padx=100, pady=20, font=('times', 16), text="Stand", bg="#F5F5F5", relief=RIDGE, justify=CENTER, state=DISABLED, command=standfx)
    stand_button.place(relx=.55, rely=.3)

    dd_button = Button(player_frame, padx=75, pady=20, font=('times', 16), text="Double Down", bg="#F5F5F5", relief=RIDGE, justify=CENTER, state=DISABLED, command=ddfx)
    dd_button.place(relx=.15, rely=.5)

    repeat_button = Button(player_frame, padx=78, pady=20, font=('times', 16), text="Repeat Bet", bg="#F5F5F5", relief=RIDGE, justify=CENTER, state=DISABLED, command=repeatbetfx)
    repeat_button.place(relx=.55, rely=.5)

    deal_button = Button(player_frame, padx=70, pady=30, font=('times', 16), text="Deal/Place Bet", bg="#F5F5F5", relief=RIDGE, justify=CENTER, command=dealfx)
    deal_button.place(relx=.35, rely=.70)

    cam_frame = LabelFrame(main_right, width=.25*max_width, height=.3*max_height, bg="cyan", text="Live Camera", font=('times', 16), labelanchor=N)
    cam_frame.pack_propagate(0)
    cam_frame.pack(side=TOP)

    status_frame = LabelFrame(main_right, width=.25*max_width, height=.6*max_height, bg="#F5F5F5", text="Log & Status", font=('times', 16), labelanchor=N)
    status_frame.pack_propagate(0)
    status_frame.pack(side=TOP)

    scroll = Scrollbar(status_frame)
    scroll.pack(side=RIGHT, fill=Y)

    text_log = Text(status_frame, font=('times', 11), width=62, height=100, bg="#303030", fg="#00ef2b", yscrollcommand=scroll.set)
    text_log.pack(side=LEFT, fill=Y)
    scroll.config(command=text_log.yview)
    text_log.yview_pickplace("End")

    if not armstat.ino_setup:
        print_log("Arduino Setting Up...")
        armstat.ino_setup = True
        mega = pyfirmata.Arduino('COM5')  # This might change depending on the computer.
        it = pyfirmata.util.Iterator(mega)
        it.start()
        led1 = mega.get_pin('d:4:o')
        led2 = mega.get_pin('d:5:o')
        led3 = mega.get_pin('d:6:o')
        busy = mega.get_pin('d:3:i')
        print_log("Arduino Ready!")

    window.mainloop()
    mega.exit()
