from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *
from PyQt5.QtTest import *

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()

        print('<키움 클래스 입니다>')

        ########### 이벤트 loog 모음
        self.login_event_loop = None
        self.detail_account_info_event_loop = QEventLoop()
        self.calculator_event_loop = QEventLoop()
        ############################

        ############## 스크린 번호 모음
        self.screen_my_info = '2000'
        self.screen_calculation_stock = '4000'
        ############################

        ############  변수 모음
        self.account_num = None
        self.account_stock_dict = {}
        self.not_account_stock_dict = {}
        ##########################

        #########  계좌 관련 변수
        self.use_money = 0
        self.use_money_percent = 0.5
        ##########################

        ####### 종목 분석 용
        self.calcul_data = []
        #####################


        self.get_ocx_instance()
        self.event_slots()
        self.signal_login_commConnect()    #로그인
        self.get_account_info()    #계좌번호 가져오기
        self.detail_account_info() # 예수금 가져오기
        self.detail_account_mystock() # 계좌평가 잔고내역 요청
        self.not_concluded_account() # 미체결 요청

        self.calculator_fnc()  #종목 분석용(임시)



    def get_ocx_instance(self):
        self.setControl('KHOPENAPI.KHOpenAPICtrl.1')

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.trdata_slot)

    def login_slot(self, errCode):
        print(errCode)

        self.login_event_loop.exit()

    def signal_login_commConnect(self):        #로그인 시도
        self.dynamicCall('CommConnect()')

        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def login_slot(self, errCode):
        print(errCode)
        print(errors(errCode))

        self.login_event_loop.exit()

    def get_account_info(self):
        account_list = self.dynamicCall('GetLogininfo(QString)', 'ACCNO') #계좌번호

        account_num = account_list.split(';')[0]
        self.account_num = account_num
        print('나의 보유 계좌번호 %s' % self.account_num) #8156226411

    def detail_account_info(self):
        print('<예수금 요청 부분>')

        self.dynamicCall('SetInputValue(QString, QString)', '계좌번호', self.account_num)
        self.dynamicCall('SetInputValue(QString, QString)', '비밀번호', 0000)
        self.dynamicCall('SetInputValue(QString, QString)', '비밀번호입력매체구분', 00)
        self.dynamicCall('SetInputValue(QString, QString)', '조회구분', 2)
        self.dynamicCall('CommRqData(QString, QString, int, QString)', '예수금상세현황요청','opw00001', '0', self.screen_my_info)
        self.detail_account_info_event_loop.exec_()

    def detail_account_mystock(self, sPrevNext='0'):
        print('<계좌평가 잔고내역 연속 조회> %s' % sPrevNext)
        self.dynamicCall('SetInputValue(QString, QString)', '계좌번호', self.account_num)
        self.dynamicCall('SetInputValue(QString, QString)', '비밀번호', 0000)
        self.dynamicCall('SetInputValue(QString, QString)', '비밀번호입력매체구분', 00)
        self.dynamicCall('SetInputValue(QString, QString)', '조회구분', 2)
        self.dynamicCall('CommRqData(QString, QString, int, QString)', '계좌평가잔고내역요청', 'opw00018', sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def not_concluded_account(self, sPrevNext='0'):
        print('미체결 요청')

        self.dynamicCall('SetInputValue(QString, QString)', '계좌번호', self.account_num)
        self.dynamicCall('SetInputValue(QString, QString)', '체결구분', '1')
        self.dynamicCall('SetInputValue(QString, QString)', '매매구분', '0')
        self.dynamicCall('CommRqData(QString, QString, int, QString)', '실시간미체결요청', 'opt10075', sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()




    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        '''
        tr요청을 받는 구역
        :param sScrNo: 스크린번호
        :param sRQName: 내가 요청했을 때 지은 이름
        :param sTrCode: 요청id, tr코드
        :param sRecordName: 사용 안함
        :param sPrevNext: 다음 페이지가 있는지
        :return:
        '''

        if sRQName == '예수금상세현황요청':
            deposit = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, 0,'예수금')

            print('예수금 %s' % deposit)
            print('예수금 형태 변환 %s' % int(deposit))

            self.use_money = int(deposit) * self.use_money_percent
            self.use_money = self.use_money / 4

            ok_deposit = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, 0,'출금가능금액')
            print('출금가능금액 %s' % ok_deposit)
            print('출금가능금액 형태 변환 %s' % int(ok_deposit))

            self.detail_account_info_event_loop.exit()



        if sRQName == '계좌평가잔고내역요청':
            total_buy_money = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, 0,'총매입금액')
            total_buy_money_result = int(total_buy_money)

            print('총매입금액 %s' % total_buy_money_result)

            total_profit_loss_rate = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, 0,'총수익률(%)')
            total_profit_loss_rate = float(total_profit_loss_rate)

            print('총수익률(%%) : %s' % total_profit_loss_rate)

            rows = self.dynamicCall('GetRepeatCnt(Qstring, Qstring)', sTrCode, sRQName)
            cnt = 0
            for i in range(rows):
                code = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '종목번호')
                code = code.strip()[1:]

                code_nm = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '종목명')
                stock_quantity = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '보유수량')
                buy_price = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '매입가')
                learn_rate = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '수익률(%)')
                current_price = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '현재가')
                total_chegual_price = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '매입금액')
                possible_quantity = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '매매가능수량')

                if code in self.account_stock_dict:
                    pass
                else:
                    self.account_stock_dict.update({code:{}})

                code_nm = code_nm.strip()
                stock_quantity = int(stock_quantity.strip())
                buy_price = int(buy_price.strip())
                learn_rate = float(learn_rate.strip())
                current_price = int(current_price.strip())
                total_chegual_price = int(total_chegual_price.strip())
                possible_quantity = int(possible_quantity.strip())

                self.account_stock_dict[code].update({'종목명': code_nm})
                self.account_stock_dict[code].update({'보유수량': stock_quantity})
                self.account_stock_dict[code].update({'매입가': buy_price})
                self.account_stock_dict[code].update({'수익률(%)': learn_rate})
                self.account_stock_dict[code].update({'현재가': current_price})
                self.account_stock_dict[code].update({'매입금액': total_chegual_price})
                self.account_stock_dict[code].update({'매입가능수량': possible_quantity})

                cnt += 1

            print('계좌에 가지고 있는 종목 %s' % self.account_stock_dict)
            print('계좌에 가지고 있는 종목 수 : %s' % cnt)

            if sPrevNext == '2':
                self.detail_account_mystock(sPrevNext='2')
            else:
                self.detail_account_info_event_loop.exit()


        elif sRQName == '실시간미체결요청':

            rows = self.dynamicCall('GetRepeatCnt(Qstring, Qstring)', sTrCode, sRQName)

            for i in range(rows):
                code = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '종목번호')
                code_nm = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '종목명')
                order_no = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '주문번호')
                order_status = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '주문상태') #접수, 확인, 체결
                order_quantity = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '주문수량')
                order_price = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '주문가격')
                order_gubun = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '주문구분') #매도, 매수, 정정, 취소
                not_quantity = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '미체결수량')
                ok_quantity = self.dynamicCall('GetCommData(Qstring, Qstring, int, QString)', sTrCode, sRQName, i, '체결량')

                code = code.strip()
                code_nm = code_nm.strip()
                order_no = int(order_no.strip())
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())
                order_gubun = order_gubun.strip().lstrip('+').lstrip('-')
                not_quantity = int(not_quantity.strip())
                ok_quantity = int(ok_quantity.strip())

                if order_no in self.not_account_stock_dict:
                    pass
                else:
                    self.not_account_stock_dict[order_no] = {}

                self.not_account_stock_dict[order_no].update({'종목코드': code})
                self.not_account_stock_dict[order_no].update({'종목명': code_nm})
                self.not_account_stock_dict[order_no].update({'주문번호': order_no})
                self.not_account_stock_dict[order_no].update({'주문상태': order_status})
                self.not_account_stock_dict[order_no].update({'주문수량': order_quantity})
                self.not_account_stock_dict[order_no].update({'주문가격': order_price})
                self.not_account_stock_dict[order_no].update({'주문구분': order_gubun})
                self.not_account_stock_dict[order_no].update({'미체결수량': not_quantity})
                self.not_account_stock_dict[order_no].update({'체결량': ok_quantity})

                print('미체결 종목 : %s' % self.not_account_stock_dict[order_no])


            self.detail_account_info_event_loop.exit()

        elif "주식일봉차트조회" == sRQName:

            code = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, 0, '종목코드')
            code = code.strip()
            print('%s 일봉데이터 요청' % code)

            cnt = self.dynamicCall('GetRepeatCnt(Qstring, Qstring)', sTrCode, sRQName)
            print('데이터 일수 %s' % cnt)

            # data = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName)
            # [['', '현재가', '거래량', '거래대금', '날짜', '시가', '고가', '저가', '']]

            #한 번 조회하면 600일의 일봉 데이터 조회 가능
            for i in range(cnt):
                data = []

                current_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '현재가')
                value = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '거래량')
                trading_value = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '거래대금')
                date = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '일자')
                start_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '시가')
                high_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '고가')
                low_price = self.dynamicCall('GetCommData(QString, QString, int, QString)', sTrCode, sRQName, i, '저가')

                data.append('')
                data.append(current_price.strip())
                data.append(value.strip())
                data.append(trading_value.strip())
                data.append(date.strip())
                data.append(start_price.strip())
                data.append(high_price.strip())
                data.append(low_price.strip())
                data.append('')

                self.calcul_data.append(data.copy())

            print(len(self.calcul_data))

            if sPrevNext == '2':
                self.day_kiwoon_db(code=code, sPrevNext=sPrevNext)

            else:

                print('총 일수 %s' % len(self.calcul_data))

                pass_success = False

                # 120일 이평선을 그릴 만큼의 데이터가 있는지 확인
                if self.calcul_data == None or len(self.calcul_data) < 120:
                    pass_success = False

                else:
                    # 120일 이평선을 그릴 만큼 데이터가 있으면
                    total_price = 0
                    for value in self.calcul_data[:120]:
                        total_price += int(value[1])

                    moving_average_price = total_price / 120

                    #오늘자 주가가 120일 이평선에 걸쳐있는지 확인
                    bottom_stock_price = False
                    check_price = None
                    if int(self.calcul_data[0][7]) <= moving_average_price and moving_average_price <= int(self.calcul_data[0][6]):
                        # 120이평선이 오늘 저가보다 높고 오늘 고가보다 낮다
                        print('오늘 주가가 120 이평선에 걸쳐있는 것 확인')
                        bottom_stock_price = True
                        check_price = int(self.calcul_data[0][6])

                    # 과거 일봉들이 120일 이평선보다 밑에 있는지 확인
                    # 그렇게 확인 하다 일봉이 120일 이평선보다 위에 있으면 계산 진행
                    prev_price = None
                    if bottom_stock_price == True:

                        moving_average_price_prev = 0
                        price_top_moving = False

                        idx = 1
                        while True:

                            if len(self.calcul_data[idx:]) < 120: # 120치가 있는지 계속 확인
                                print('120일치 일봉 데이터가 없음')
                                break

                            total_price = 0
                            for value in self.calcul_data[idx:120+idx]:
                                total_price += int(value[1])
                            moving_average_price_prev = total_price / 120

                            if moving_average_price_prev <= int(self.calcul_data[idx][6]) and idx <= 20:
                                print('20일 동안 주가가 120일 이평선과 같거나 위에 있으면 조건 통과 못함')
                                price_top_moving = False
                                break

                            elif int(self.calcul_data[idx][7]) > moving_average_price_prev and idx > 20:
                                print('120일 이평선 위에 있는 일봉 확인됨')
                                price_top_moving = True
                                prev_price = int(self.calcul_data[idx][7])
                                break

                            idx += 1

                        # 해당 이평선이 가장 최근 일자의 이평선 가격보다 낮은지 확인
                        if price_top_moving == True:
                            if moving_average_price > moving_average_price_prev and check_price > prev_price:
                                print('포착된 이평선의 가격이 오늘자(최근일자) 이평선 가격보다 낮은 것 확인')
                                print('포착된 일봉 저가가 오늘자 일봉 고가보다 낮은지 확인')
                                pass_success = True

                if pass_success == True:
                    print('조건부 통과됨')

                    code_nm = self.dynamicCall('GetMasterCodeName(QString)', code)

                    f = open('files/condition_stock.txt', 'a', encoding='utf8')
                    f.write('%s\t%s\t%s\n' % (code, code_nm, str(self.calcul_data[0][1])))
                    f.close()

                elif pass_success == False:
                    print('조건 통과 못함')


                self.calcul_data.clear()
                self.calculator_event_loop.exit()


    def get_code_list_by_market(self, market_code):
        '''
        종목 코드 반환
        :param market_code:
        :return:
        '''

        code_list = self.dynamicCall('GetCodeListByMarket(QString)', market_code)
        code_list = code_list.split(';')[:-1]

        return code_list


    def calculator_fnc(self):

        '''
        종목 분석 실행용
        :return:
        '''

        code_list = self.get_code_list_by_market('10')
        print('코스닥 개수 %s' % len(code_list))

        for idx, code in enumerate(code_list):

            self.dynamicCall('DisconnectRealData(QString)', self.screen_calculation_stock)

            print('%s / %s : KOSDAQ Stock Code : %s is updating...' % (idx+1, len(code_list), code))

            self.day_kiwoon_db(code=code)


    def day_kiwoon_db(self, code=None, date=None, sPrevNext='0'):

        QTest.qWait(3600)

        self.dynamicCall('SetInputValue(QString,QString)', '종목코드', code)
        self.dynamicCall('SetInputValue(QString,QString)', '수정주가구분', '1')

        if date != None:
            self.dynamicCall('SetInputValue(QString,QString)', '기준일자', date)

        self.dynamicCall('CommRqData(QString,QString, int, QString)', '주식일봉차트조회', 'opt10081', sPrevNext, self.screen_calculation_stock)

        self.calculator_event_loop.exec_()










