"""
Connor Callison
8/18/17
connor@humboldt.edu
Alma Bursar Export -> Data Conversoin Script

***PRODUCTION VERSION***
*** 1.0.0 ***

This script will read the specified Alma export file, and convert
it to the required format to be importe into PeopleSoft.
"""
from lxml import etree
import csv
import time
from os import rename as mv
from os import listdir
import shutil

archival_path = 'old_xml/'
# Path for converted files to be written.
student_output_file_path = 'output/bursar-converted-%s-%s.dat' % ('DEBITS', time.strftime("%d%m%Y"))
community_output_file_path = 'output/bursar-community-%s.csv' % (
    time.strftime("%d%m%Y"))

# Namespace map for XML processing
nsm = {"xb": "http://com/exlibris/urm/rep/externalsysfinesfees/xmlbeans"}

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
    input_file_name = ''
    xml_count = 0
    for file in listdir('.'):
        if file.endswith(".xml"):
            input_file_name = file
            xml_count += 1

    if xml_count > 1:
        print "There are %s '.xml' files in this directory. There can only be one." % (xml_count)
        print "Please remove any .xml files that are not the target file and try again."
        quit()

    elif xml_count == 0:
        print "No '.xml' file found. Please place the target file in the same directory as this script."
        quit()

    else:
        return input_file_name


def parse_data(input_file):
    print "Converting Data..."
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
    campus_count = 0
    campus_debits = 0
    campus_credits = 0
    community_count = 0
    community_debits = 0
    community_credits = 0


    for user in all_users:
        if user.user_type == 'campus':
            campus_count += 1
            for fee in user.get_fees():
                amount = float(fee.amount)
                fee_type = fee.lib_code
                if fee_type != 'CREDIT':
                    campus_debits += amount
                else:
                    campus_credits += amount
        else:
            community_count += 1
            for fee in user.get_fees():
                amount = float(fee.amount)
                fee_type = fee.lib_code
                if fee_type != 'CREDIT':
                    community_debits += amount
                else:
                    community_credits += amount

    print "Campus users:", campus_count
    print "Campus debits: $" + str(campus_debits)
    print "Campus credits: $" + str(campus_credits)
    print "--"
    print "Community users:", community_count
    print "Community debits: $" + str(community_debits)
    print "Community credits: $" + str(community_credits)
    print "----"
    print "Total debits: $" + str(campus_debits + community_debits)
    print "Total credits: $" + str(campus_credits + community_credits)
    print "Gross total: $" + str((campus_debits + community_debits) - (campus_credits + community_credits))


def is_campus_user(username):
    if len(username) == 9 and username[0] in ['0','9']:
        return True
    else:
        return False


def clear_output_dir():
    output_path = 'output/'
    input_file_name = ''
    for file in listdir(output_path):
        if file.endswith(".dat") or file.endswith(".csv") :
            input_file_name = file
            shutil.move(output_path + input_file_name, output_path + 'old/' + input_file_name)


def main():
    print "----", time.ctime(), "----"
    input_file_name = find_file()
    all_users = parse_data(input_file_name)
    clear_output_dir()
    write_data(all_users, student_output_file_path, community_output_file_path)
    gather_stats(all_users)
    archive_file( input_file_name, archival_path)


if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        print 'Error:', e