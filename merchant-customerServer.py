import socket
import random
from cryptography.fernet import Fernet
import math
import time
import pymongo

# Establish MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
database = client["payment_database"]
collection = database["transactions"]

ip = '127.0.0.1'
print("***********************************Customer and Merchant Side**********************************************")
senderSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiverSocket.bind((ip, 5004))

bankBalanceDatabase = {"BK456783": 345, "BK459843": 90567, "BK635485": 640}

key = Fernet.generate_key()
k = Fernet(key)

print("User has bought the items... ")
orderAmount = int(input("The total amount that user needs to pay is "))
thresholdAmount = 300
actualTransactions = math.ceil(orderAmount / thresholdAmount)
successfullTransactions = 0
loopCounter = 0
print("Enter Y to continue...")
check = input()
continueCheck = ''

if check == 'Y' or check == 'y':
    print("Enter the debit card number of the User...")
    debitCardNumber = input()

    if bankBalanceDatabase[debitCardNumber] < orderAmount:
        print("In-Sufficient balance")
        print("Press 1 to enter another bank account and continue the transaction else to cancel the transaction...")
        continueCheck = input()
        if continueCheck == '1':
            print("Enter the second debit card number...")
            secondDebitCardNumber = input()
        else:
            print("You have chosen not to continue due to insufficient balance...")
            exit()

        if bankBalanceDatabase[secondDebitCardNumber] >= orderAmount:
            debitCardNumber = secondDebitCardNumber
            continueCheck = ' '

    print("Enter the Acc number of the merchant...")
    merchantCardNumber = input()

    while loopCounter != actualTransactions:
        if loopCounter + 1 == actualTransactions:
            currentAmount = orderAmount % thresholdAmount
        else:
            currentAmount = thresholdAmount

        if continueCheck == '1':
            bankDetails = "*" + debitCardNumber + "&" + secondDebitCardNumber + "@" + merchantCardNumber + "#" + str(
                currentAmount)
        else:
            bankDetails = "*" + debitCardNumber + "@" + merchantCardNumber + "#" + str(currentAmount)

        bankDetailsBytes = bankDetails.encode()  # convert string to bytes
        encryptedMessageBytes = k.encrypt(bankDetailsBytes)  # encrypt the bytes
        print(encryptedMessageBytes)
        encryptedMessage = encryptedMessageBytes.decode("utf-8")  # decode to add the key for decoding at gateway
        encryptedMessage = key.decode("utf-8") + encryptedMessage  # key is converted into string and added to string
        sentTime = time.time()
        sentTime = math.floor(sentTime)
        encryptedMessage = str(sentTime) + "." + encryptedMessage  # timestamp is added
        senderSocket.sendto(encryptedMessage.encode(), (ip, 5003))  # send the encoded data to the gateway
        gatewayData, addr = receiverSocket.recvfrom(1024)
        if gatewayData.decode() == "Y":
            successfullTransactions += 1

    #if successfullTransactions == actualTransactions:
        print("Successfull Transaction. Order Placed. Order number is " + str(random.randint(99999, 100000045)) + " .")

        # Storing transaction data in MongoDB
        for i in range(actualTransactions):
            transaction_data = {
                "debit_card_number": debitCardNumber,
                "merchant_card_number": merchantCardNumber,
                "amount": currentAmount,
                "timestamp": sentTime
            }
            collection.insert_one(transaction_data)

        if continueCheck == '1':
            remainingAmt = bankBalanceDatabase[debitCardNumber] + bankBalanceDatabase[
                secondDebitCardNumber] - orderAmount
            print("Available balance for Account number " + debitCardNumber + " is " + str(
                math.ceil(remainingAmt / 2)) + " .")
            print("Available balance for Account number " + secondDebitCardNumber + " is " + str(
                math.floor(remainingAmt / 2)) + " .")
        else:
            print("Available balance for User having Account number " + debitCardNumber + " is " + str(
                bankBalanceDatabase[debitCardNumber] - orderAmount) + " .")

    else:
        print("Unsuccessfull Transaction. Try Again later.")
else:
    print("You have wished not to continue. Have a good day :)")

senderSocket.close()
receiverSocket.close()
