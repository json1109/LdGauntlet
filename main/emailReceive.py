# encoding: utf-8
import imaplib, email,os,re
import sys
import traceback

""" 
邮件获取类
"""

class EmailService(object):
    EMAIL_SERVER={
        "QQ":{"SMTP":["smtp.qq.com",465,True],"POP3":["pop.qq.com",995,True],"IMAP":["imap.qq.com",993,True]},
        "GMAIL":{"SMTP":["smtp.gmail.com",465,True],"POP3":["pop.gmail.com",995,True],"IMAP":["imap.gmail.com",993,True]},
        "FOXMAIL":{"SMTP":["SMTP.foxmail.com",465,True],"POP3":["POP3.foxmail.com",995,True],"IMAP":["imap.foxmail.com",993,True]},
        "SINA":{"SMTP":["smtp.sina.com.cn",465,True],"POP3":["pop3.sina.com.cn",995,True],"IMAP":["imap.sina.com",993,True]},
        "163":{"SMTP":["smtp.163.com",465,True],"POP3":["pop.163.com",995,True],"IMAP":["imap.163.com",993,True]},
        "HOTMAIL":{"SMTP":["smtp.live.com",25,False],"POP3":["pop.live.com",995,True],"IMAP":["imap.live.com",993,True]},
        "OUTLOOK":{"SMTP":["smtp-mail.outlook.com",25,False],"POP3":["pop-mail.outlook.com",995,True],"IMAP":["imap-mail.outlook.com",993,True]},
        "AOL":{"SMTP":["smtp.aol.com",25,False],"POP3":["pop.aol.com",110,False],"IMAP":["imap.aol.com",993,True]},
        "YAHOO":{"SMTP":["smtp.mail.yahoo.com",465,True],"POP3":["pop.mail.yahoo.com",995,True],"IMAP":["imap.mail.yahoo.com",993,True]},
        "21CN": {"SMTP": ["smtp.21cn.com", 465, True], "POP3": ["pop.21cn.com", 995, True],"IMAP": ["imap.21cn.com", 143, False]},
        "MAIL": {"SMTP": ["smtp.mail.ru", 465, True], "POP3": ["pop.mail.ru", 995, True],"IMAP": ["imap.mail.ru", 993, True]},
    }

    @staticmethod
    def __getEmailServer(emailtype,servertype):
        return EmailService.EMAIL_SERVER.get(emailtype.upper()).get(servertype)

    @staticmethod
    def getSMTPServer(emailtype):
        return EmailService.__getEmailServer(emailtype.upper(),'SMTP')

    @staticmethod
    def getPOPServer(emailtype):
        return EmailService.__getEmailServer(emailtype.upper(),'POP3')

    @staticmethod
    def getIMAPServer(emailtype):
        return EmailService.__getEmailServer(emailtype.upper(),'IMAP')

class EmailReceive(object):
    def __init__(self,emailAddress,authorityCode):
        self.imap_mail = None
        self.__login(emailAddress,authorityCode)

    def __login(self,address,password):
        try:
            serverInfo=EmailService.getIMAPServer(address.split('@')[-1].split('.')[0])
            if serverInfo[2]:
                self.imap_mail = imaplib.IMAP4_SSL(serverInfo[0],serverInfo[1])
            else:
                self.imap_mail = imaplib.IMAP4(serverInfo[0], serverInfo[1])
            self.imap_mail.login(address,password)
        except Exception as e:
            print(e)

    def close(self):
        self.imap_mail.close()
        self.imap_mail.logout()

    def getEmail(self,keyword=None,onlyUnsee=True,findAll=False,getAttach=False):
        result=[]
        try:
            self.imap_mail.select()
        except Exception as e:
            print(e)
            return result
        num_index = 0
        for item in self.imap_mail.list()[1]:
            box = item.decode().split(' \"/\" ')[-1]
            if  re.match(r'.*?(Sent|Delete|Trash|Draft).*?',box,re.M|re.I):
                continue
            try:
                if num_index != 0:
                    self.imap_mail.select(box)
                num_index += 1
                if onlyUnsee:
                    try:
                        state, en = self.imap_mail.search(None, 'UNSEE')
                    except Exception as e:
                        state, en = self.imap_mail.search(None, 'ALL')
                else:
                    state, en = self.imap_mail.search(None,'ALL')
                for num in en[0].split()[::-1]:
                    typ, data = self.imap_mail.fetch(num, '(RFC822)')
                    header = EmailReceive.getMailHeader(data)
                    print(header)
                    if header is None:
                        continue
                    if keyword is None:
                        result.append(EmailReceive.getOneMail(data, getAttach))
                    else:
                        for keyItem in keyword:
                            if keyItem in header[0] or keyItem in header[1] or keyItem in header[2]:
                                result.append(EmailReceive.getOneMail(data,getAttach))
                                if not findAll:
                                    self.close()
                                    return result
            except Exception as e:
                traceback.print_exc()
                print('getEmail',e)
        self.close()
        return result

    @staticmethod
    def getMailHeader(data):
        if data is None or data[0] is None or data[0][1] is None:
            return None
        try:
            message = email.message_from_bytes(data[0][1])
            return EmailReceive.__parseHeader(message)
        except Exception as e:
            print('getMailHeader',e)
            return None

    @staticmethod
    def getMailBody(data,getAttach=False):
        if data is None or data[0] is None or data[0][1] is None:
            return None
        try:
            message = email.message_from_bytes(data[0][1])
            return EmailReceive.__parseBody(message,getAttach)
        except Exception as e:
            print('getMailBody',e)
            return None

    @staticmethod
    def getOneMail(data,getAttach=False):
            if data is None or data[0] is None or data[0][1] is None:
                return None,None
            try:
                message = email.message_from_bytes(data[0][1])
                header = EmailReceive.__parseHeader(message)
                body = EmailReceive.__parseBody(message,getAttach)
                return header,body
            except Exception as e:
                print('getOneMail',e)
                return None,None

    @staticmethod
    def __parseHeader(message):
        """ 解析邮件首部 """
        try:
            if not message.get('Subject'):
                title=''
            else:
                title = email.header.decode_header(message.get('Subject'))
                if title[0][1] is not None:
                    encodetype = title[0][1]
                    if 'unknow' in encodetype:
                        # encodetype='GBK'
                        encodetype='utf-8'
                    title = title[0][0].decode(encodetype)
                else:
                    title = title[0][0]
            try:        
                fromAddr = email.utils.parseaddr(message.get('from'))[1]
            except Exception as e:
                fromAddr = ''
            toAddr = email.utils.parseaddr(message.get('to'))[1]
            receiveDate = email.utils.parsedate(message.get('Date'))
            receiveDate=str(receiveDate[0])+'-'+str(receiveDate[1]).zfill(2)+'-'+str(receiveDate[2]).zfill(2)
            result = (title,fromAddr,toAddr,receiveDate)
            return result
        except Exception as e:
            # traceback.print_exc()
            print('__parseHeader',e)
            return None

    @staticmethod
    def __parseBody(msg,getAttach=False):
        context=[]
        try:
            for par in msg.walk():
                if par.is_multipart():
                    continue
                patch = par.get_param("name")  # 如果是附件，这里就会取出附件的文件名
                if patch:# 有附件
                    print(patch)
                else:
                    try:
                        context.append(par.get_payload(decode=True).decode('utf-8'))
                    except Exception as e:
                        print(e)
                        context.append(par.get_payload(decode=True).decode('gbk'))
            return context
        except Exception as e:
            print('__parseBody',e)
            return None



