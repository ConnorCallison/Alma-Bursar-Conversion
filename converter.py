"""
Connor Callison
8/18/17
connor@humboldt.edu
Alma Bursar Export -> Data Conversoin Script

***PRODUCTION VERSION***
*** 1.0.2 ***

This script will read the specified Alma export file, and convert
it to the required format to be importe into PeopleSoft.
"""
from lxml import etree
import csv
import time
from os import chdir
from os import rename as mv
from os import listdir
import shutil
import smtplib

archival_path = 'old_xml/'
# Path for converted files to be written.
student_output_file_path = 'output/bursar-converted-%s-%s.dat' % ('DEBITS', time.strftime("%d%m%Y"))
community_output_file_path = 'output/bursar-community-%s.csv' % (
    time.strftime("%d%m%Y"))

# Namespace map for XML processing
nsm = {"xb": "http://com/exlibris/urm/rep/externalsysfinesfees/xmlbeans"}

# This dictionary allows us to switch out the library fee types for the 
# corresponding PeopleSoft item_type.
item_type_map = {'LIBRARYCARDREPLACEMENT': '300000005921',
                 'LOSTITEMPROCESSFEE': '300000006918',
                 'OVERDUEFINE': '300000006919',
                 'CREDIT': '820000206129',
                 'LOSTITEMREPLACEMENTFEE': '300000006920'}

class User:

    def __init__(self, username, name, user_type = 'campus'):
        self.username = username
        self.fees = []
        self.user_type = user_type
        self.name = name

    def add_fee(self, fee):
        self.fees.append(fee)

    def get_fees(self):
        return self.fees

    def set_type(self, user_type):
        self.user_type = user_type


class Fee:

    def __init__(self, term, lib_code, amount, date):
        self.term = term
        self.lib_code = lib_code
        self.amount = amount
        self.date = date


def find_file():
    """
    Looks for the .XML file in the current woeking directory.

    NOTE: There can only be one .XML file present.
    """
    input_file_name = ''
    xml_count = 0
    for file in listdir('.'):
        if file.endswith(".xml"):
            input_file_name = file
            xml_count += 1

    if xml_count > 1:
        error = "There are %s '.xml' files in this directory. There can only be one." % (xml_count)
        error += "\nPlease remove any .xml files that are not the target file and try again."
        raise Exception(error)

    elif xml_count == 0:
        error = "No '.xml' file found. The file transfer from Alma may have failed."
        raise Exception(error)

    else:
        return input_file_name


def parse_data(input_file):
    """
    Takes in an input file, loads the XML into a tree
    traverses the file and grabs out fees and associates them
    with a user.

    Returns list of User objects.
    """
    print "Converting Data..."

    # Load XML into tree / find fees.
    users = []
    tree = etree.parse(open(input_file))
    root = tree.getroot()
    userExportedFineFees_list = root.findall(
        'xb:userExportedFineFees', namespaces=nsm)
    userExportedFineFees = userExportedFineFees_list[1]
    userExportedList = userExportedFineFees.find(
        'xb:userExportedList', namespaces=nsm)
    userExportedFineFeesList = userExportedList.findall(
        'xb:userExportedFineFeesList', namespaces=nsm)

    # Create instances of User and add their fees.
    for user_fees in userExportedFineFeesList:
        user = user_fees.find('xb:user', namespaces=nsm)
        username = user.find('xb:value', namespaces=nsm).text
        name = user_fees.find('xb:patronName', namespaces=nsm).text

        new_user = User(username, name)

        fee_list_elem = user_fees.find('xb:finefeeList', namespaces=nsm)
        for item in fee_list_elem:

            new_fee = None
            fee_type = item.find('xb:fineFeeType', namespaces=nsm).text
            txn_dt = item.find('xb:lastTransactionDate', namespaces=nsm).text
            amount = item.find('xb:compositeSum', namespaces=nsm).find(
                'xb:sum', namespaces=nsm).text
            date = item.find('xb:lastTransactionDate', namespaces=nsm).text.split(' ')[0]

            if float(amount) < 0:
                new_fee = Fee(1234, 'CREDIT', str(float(amount) * -1), date)
            elif float(amount) > 0:
                new_fee = Fee(1234, fee_type, amount, date)

            new_user.add_fee(new_fee)

        if is_campus_user(new_user.username):
            users.append(new_user)
        else:
            new_user.set_type('community')
            users.append(new_user)

    return users


def write_data(user_list, student_file_name, community_file_name):
    """
    Takes in a list of Users, student file name, and community file name.
    Seperates the users by USEER ID, and seperates the users into their correspinding
    files.
    """
    student_output_file = open(student_file_name, 'w')
    output_credits = open(student_file_name.replace('DEBITS','CREDITS'), 'w')
    community_output_file = open(community_file_name, 'w')
    community_output_file.write('UserID' + ',' + 'Name' + ',' + 'Item Type' + ',' +'Amount' + ',' + 'Date\n')

    for user in user_list:
        if user.user_type == 'campus':
            for fee in user.get_fees():
                if item_type_map[str(fee.lib_code)] == '820000206129':
                    output_credits.write(str(user.username) + ',' + item_type_map[str(fee.lib_code)] + 
                        ',' + str('{:07.2f}'.format(float(fee.amount))) + ',' + fee.date + '\n')
                else:
                    student_output_file.write(str(user.username) + ',' + item_type_map[str(fee.lib_code)] + 
                        ',' + str('{:07.2f}'.format(float(fee.amount))) + ',' + fee.date + '\n')
        else:
            for fee in user.get_fees():
                community_output_file.write(str(user.username) + ','
                                            +  '"' + str(user.name) + '"' + ','
                                            + str(fee.lib_code) + ',' 
                                            + str('{:07.2f}'.format(float(fee.amount))) + ','
                                            + fee.date + '\n')


def archive_file( input_file_name, path):
    """
    This function simply moves one file to another location.
    Its purpose is to move the xml file after it has undergone conversion
      to the archival path.
    """
    mv(input_file_name, path + input_file_name)


def gather_stats(all_users):
    """
    Gethers basic statistics about what was read from the XML.
    Best used for for basic validation of totals between files.
    """
    campus_count = 0
    campus_debits = 0
    campus_debit_count = 0
    campus_credits = 0
    campus_credit_count =0
    community_count = 0
    community_debits = 0
    community_credits = 0
    output_string = ''


    for user in all_users:
        if user.user_type == 'campus':
            campus_count += 1
            for fee in user.get_fees():
                amount = float(fee.amount)
                fee_type = fee.lib_code
                if fee_type != 'CREDIT':
                    campus_debits += amount
                    campus_debit_count += 1
                else:
                    campus_credits += amount
                    campus_credit_count += 1
        else:
            community_count += 1
            for fee in user.get_fees():
                amount = float(fee.amount)
                fee_type = fee.lib_code
                if fee_type != 'CREDIT':
                    community_debits += amount
                else:
                    community_credits += amount

    output_string += "\nCampus users: " + str(campus_count)
    output_string += "\nCampus debits: $" + str(campus_debits) + ' | Transactions: ' + str(campus_debit_count)
    output_string += "\nCampus credits: $" + str(campus_credits) + ' | Transactions: ' + str(campus_credit_count)
    output_string += "\n--"
    output_string += "\nCommunity users: " + str(community_count)
    output_string += "\nCommunity debits: $" + str(community_debits)
    output_string += "\nCommunity credits: $" + str(community_credits)
    output_string += "\n----"
    output_string += "\nTotal debits: $" + str(campus_debits + community_debits)
    output_string += "\nTotal credits: $" + str(campus_credits + community_credits)
    output_string += "\nGross total: $" + str((campus_debits + community_debits) - (campus_credits + community_credits))
    output_string += '\n'

    print output_string
    return output_string


def is_campus_user(username):
    """
    This function is used to identify if a user ID is a valid
    university ID.
    """
    if len(username) == 9 and username[0] in ['0','9']:
        return True
    else:
        return False


def clear_output_dir():
    """
    Moves previous output files into an archival directory.
    """
    output_path = 'output/'
    input_file_name = ''
    for file in listdir(output_path):
        if file.endswith(".dat") or file.endswith(".csv") :
            input_file_name = file
            shutil.move(output_path + input_file_name, output_path + 'old/' + input_file_name)


def send_email(from_addr,to_addr,message):
    """
    This function sends an email.
    Params: from_addr - address where email wil be sent from.
            to_addr - address where email will ve sent.
            message - string containing the content of the email.
    """
    try:
        smtpObj = smtplib.SMTP('smtp.humboldt.edu')
        smtpObj.sendmail(from_addr, to_addr,message)
        print "Email Sent!"
    except Exception, e:
        print "Email sending failed:", e


def send_success_email(stats):
    """
    Sends an email notfying of script success and
    delivers basic stats of the run using gather_stats()
    """
    message = "Subject: Bursar Data Conversion - SUCCESS"
    message += "\nTo: Library Billing Support <library-billing-support@humboldt.edu>"
    message += "\nFrom: HSU Student Finance Jobs <no-reply@humboldt.edu>"
    message += "\nThe Alma Bursar conversion script executed successfully!"
    message += "\nBelow are the metrics:\n"
    message += stats
    send_email('no-reply@humboldt.edu','library-billing-support@humboldt.edu',message)


def send_failure_email(error):
    """
    sends an email notifying users of script failure to generate files.
    The error is incluede in the email message.
    """
    message = "Subject: Bursar Data Conversion - ERROR"
    message += "\nTo: Library Billing Support <library-billing-support@humboldt.edu>"
    message += "\nFrom: HSU Student Finance Jobs <no-reply@humboldt.edu>"
    message += "\nThe Alma Bursar conversion script did not execute successfully."
    message += "\nSee error below:\n\n"

    message += str(error)

    send_email('no-reply@humboldt.edu','library-billing-support@humboldt.edu',message)


def main():
    chdir('/home/alma/bursar')
    print "----", time.ctime(), "----"
    input_file_name = find_file()
    all_users = parse_data(input_file_name)
    clear_output_dir()
    write_data(all_users, student_output_file_path, community_output_file_path)
    send_success_email(gather_stats(all_users))
    archive_file( input_file_name, archival_path)


if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        send_failure_email(e)
        print 'Error:', e