import socket
import time
from cryptography.fernet import Fernet
import msvcrt
import math
import time
import pymongo

# Establish MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
database = client["payment_database"]
collection = database["transactions"]

bankBalanceDatabase={"BK456783":345,"BK459843":90567, "BK635485":640}
bankPinDatabase = {"BK456783":6730,"BK635485":7591}
firstTransaction = True


def twoGatewayTransaction(firstDebitCard, secondDebitCard, merchantCard, Amount):
    global firstTransaction
    if firstDebitCard not in bankBalanceDatabase or secondDebitCard not in bankBalanceDatabase or merchantCard not in bankBalanceDatabase:
        return False
    elif bankBalanceDatabase[firstDebitCard] + bankBalanceDatabase[secondDebitCard] <= Amount:
        print("In-sufficient Balance in the accounts.")
        return False
    elif not firstTransaction:
        print("Processing.......")
        time.sleep(2)
        remainingAmt = bankBalanceDatabase[firstDebitCard] + bankBalanceDatabase[secondDebitCard] - Amount
        print("A sum of "+str(bankBalanceDatabase[firstDebitCard] - math.ceil(remainingAmt/2))+" has been debited from account number "+firstDebitCard +" for online purchase.")
        print("A sum of "+str(bankBalanceDatabase[secondDebitCard] - math.floor(remainingAmt/2))+" has been debited from account number "+secondDebitCard +" for online purchase.")
        bankBalanceDatabase[firstDebitCard] = math.ceil(remainingAmt/2)
        bankBalanceDatabase[secondDebitCard] = math.floor(remainingAmt/2)
        return True
    else:
        firstTransaction = False
        print("Enter the PIN for account number BK***" + firstDebitCard[5:])
        password = ""
        while True:
            x = msvcrt.getch()
            x = x.decode("utf-8")
            if x=='\r':
                break
            print('*')
            password+=x
        firstPIN = int(password)
        print("Enter the PIN for the account BK***" + secondDebitCard[5:])
        password = ""
        while True:
            x = msvcrt.getch()
            x = x.decode("utf-8")
            if x=='\r':
                break
            print('*')
            password+=x
        secondPIN = int(password)
        if bankPinDatabase[firstDebitCard] == firstPIN and bankPinDatabase[secondDebitCard] == secondPIN:
            print("Processing.......")
            time.sleep(2)
            remainingAmt = bankBalanceDatabase[firstDebitCard] + bankBalanceDatabase[secondDebitCard] - Amount
            print("A sum of "+str(bankBalanceDatabase[firstDebitCard] - math.ceil(remainingAmt/2))+" has been debited from account number "+firstDebitCard +" for online purchase.")
            print("A sum of "+str(bankBalanceDatabase[secondDebitCard] - math.floor(remainingAmt/2))+" has been debited from account number "+secondDebitCard +" for online purchase.")
            bankBalanceDatabase[firstDebitCard] = math.ceil(remainingAmt/2)
            bankBalanceDatabase[secondDebitCard] = math.floor(remainingAmt/2)
            return True
        else:
            print("Wrong PIN is entered for either of the two. Try again.")
            return False

def singleGatewayTransaction(customerCard,merchantCard,Amount):
    global firstTransaction

    if customerCard not in bankBalanceDatabase or merchantCard not in bankBalanceDatabase:
        print("Card number doesnot exist in the Database.")
        return False
    elif bankBalanceDatabase[customerCard]<Amount:
        print("In-Sufficient Balance.")
        return False
    elif not firstTransaction:
        print("Processing.......")
        time.sleep(2)
        bankBalanceDatabase[customerCard]=bankBalanceDatabase[customerCard]-Amount
        bankBalanceDatabase[customerCard]=bankBalanceDatabase[merchantCard]+Amount
        print("A sum of "+str(Amount)+" has been debited from account number "+customerCard+" for online purchase.")
        return True
    else:
        password = ""
        firstTransaction = False
        print("Enter the PIN for the account BK***" + customerCard[5:])
        while True:
            x = msvcrt.getch()
            x = x.decode("utf-8")
            if x=='\r':
                break
            print('*')
            password+=x
        PIN = int(password)
        if bankPinDatabase[customerCard] == PIN:
            print("Processing.......")
            time.sleep(2)
            bankBalanceDatabase[customerCard]=bankBalanceDatabase[customerCard]-Amount
            bankBalanceDatabase[customerCard]=bankBalanceDatabase[merchantCard]+Amount
            print("A sum of "+str(Amount)+" has been debited from account number "+customerCard+" for online purchase.")
            return True
        else:
            print("Wrong PIN entered.")
            return False


ip='127.0.0.1'
port = 5003

senderSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
receiverSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
loopBreakSignal = False
thresholdAmount = 300
receiverSocket.bind((ip,5003))
print("********************************************PAYMENT GATEWAY******************************************")

while not loopBreakSignal:
    data, addr = receiverSocket.recvfrom(1024)
    receivedTime = str(math.floor(time.time()))
    encryptedDataNKey = data.decode()
    #print(encryptedDataNKey)
    timeIndex = encryptedDataNKey.find(".")
    sentTime = encryptedDataNKey[:timeIndex]
    print("Sent TimeStamp - ",sentTime)
    print("Received TimeStamp - ",receivedTime)
    if sentTime != receivedTime:
        print("Timestamp doesnot match... Potential attack suspected...")
        msg = "N"
        senderSocket.sendto(msg.encode(),(ip,5004))
        exit()
    else:
        print("Matching Timestamp... Safe to proceed...")

    key = encryptedDataNKey[timeIndex+1:44+timeIndex+1].encode()
    #print("key is ",key.decode("utf-8"))
    k =Fernet(key)
    encryptedData = encryptedDataNKey[44+timeIndex+1:]
    bankDetailsBytes = k.decrypt(encryptedData.encode())
    bankDetails = bankDetailsBytes.decode("utf-8") #all bank details in string
    #print(bankDetails)

    index1 = bankDetails.find("*")
    index4 = bankDetails.find("&")
    index2 = bankDetails.find("@")
    index3 = bankDetails.find("#")

    if index4 == -1:
        customerBankCard = bankDetails[index1+1:index2]
        merchantBankCard = bankDetails[index2+1:index3]
        amount = int(bankDetails[index3+1:])
    else:
        customerBankCard = bankDetails[index1+1:index4]
        secondBankCard = bankDetails[index4+1:index2]
        merchantBankCard = bankDetails[index2+1:index3]
        amount = int(bankDetails[index3+1:])

    if amount != thresholdAmount:
        loopBreakSignal = True

    print("Customer Card Number ",customerBankCard)
    print("Merchant Card Number ",merchantBankCard)
    print("Amount ",amount)

    if index4 == -1:
        transactionComplete = singleGatewayTransaction(customerBankCard,merchantBankCard,amount)
    else:
        transactionComplete = twoGatewayTransaction(customerBankCard,secondBankCard,merchantBankCard,amount)

    if transactionComplete:
        msg = "Y"
    else:
        msg = "N"
        loopBreakSignal = True
    #print("Closing the server")
    if transactionComplete:
        msg = "Y"
        # Storing transaction data in MongoDB...
        transaction_data = {
            "customer_card_number": customerBankCard,
            "merchant_card_number": merchantBankCard,
            "amount": amount,
            "timestamp": sentTime,
        }
        collection.insert_one(transaction_data)
    else:
        msg = "N"
        loopBreakSignal = True
    senderSocket.sendto(msg.encode(),(ip,5004))


senderSocket.close()
receiverSocket.close()