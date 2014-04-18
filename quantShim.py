# -*- coding: utf-8 -*-  
"""
TL;DR:  
1) jump to the end of this file
2) replace "ExampleAlgo"
3) copy/paste this file to quantopian 
4) backtest
-------------

An intraday algorithmic trading framework for use with quantopian.com   
Primary use is to support multiple algorithms cooperating

@license: gpl v3

@author: JasonS@Novaleaf.com  https://PhantomJsCloud.com

disclaimer:  I'm not a fan of python so sorry if this isn't PEP compliant.


"""



# Import the libraries we will use here
import datetime
import pytz
import math
import numpy
import pandas
import scipy
import scipy.stats
import zipline

#from zipline import *
#from zipline.algorithm import *
##from zipline.api import *
#from zipline.data import *
#from zipline.errors import *
#from zipline.finance import *
#from zipline.gens import *
#from zipline.protocol import *
#from zipline.sources import *
#from zipline.transforms import *
#from zipline.utils import *
#from zipline.version import *
is_offline_Zipline = False

#quantopian shims

class WorstSpreadSlippage(slippage.SlippageModel):
    '''will trade at the worst value of the order minute.  high if long, low if short. 
    
    only meant for intraday use'''
    def __init__(self):
        #this.volume_limit = volume_limit
        pass
    def process_order(this,trade_bar,order):
        #log.info(trade_bar)
        #log.info(order)
        
        #tradeVolume = trade_bar.volume
        
        if order.amount < 0:
            price = trade_bar.low
            spread = trade_bar.close_price - trade_bar.low
        else:
            price = trade_bar.high
            spread = trade_bar.high - trade_bar.close_price
        
        #log.info(price)        
        log.info("{4} ORDER_COMMITTED: {0} shares {1} @ {2} \n\t o={5} h={6} l={7} c={8}  \t (WorstSpreadSlippage = {3:.2f}/share)"
                 .format(order.amount,trade_bar.sid.symbol,price,spread,get_datetime(),trade_bar.open_price, trade_bar.high, trade_bar.low, trade_bar.close_price))
        
        return slippage.create_transaction(
                                           trade_bar,
                                           order,
                                           price,
                                           order.amount
                                           )

class Shims():
    class Context():
        def __init__(this , portfolio=zipline.protocol.Portfolio()): #, tradingAlgorithm = zipline.TradingAlgorithm()):
            this.portfolio = portfolio
            #this.tradingAlgorithm = tradingAlgorithm
            pass
        pass

    

    class _Logger():
        '''shim for exposing the same logging definitions to visualstudio intelisence'''
        def __init__(this, framework):
            this.framework = framework
            pass    

        def error(this, message):    
            print("{0} !!ERROR!! {1}".format(this.framework.get_datetime(),message))             
            pass
        def info(this, message):
            print("{0} info {1}".format(this.framework.get_datetime(),message))            
            pass
        def warn(this, message):   
            print("{0} WARN {1}".format(this.framework.get_datetime(),message))          
            pass
        def debug(this, message):  
            print("{0} debug {1}".format(this.framework.get_datetime(),message))                           
            pass
        pass

    

    class _TradingAlgorithm_QuantopianShim:
        '''shim of zipline.TradingAlgorithm for use on quantopian '''
        def __init__(this):
            #this.logger = Shims._Logger()
            #this.logger = log
            pass
        

        def order(this,sid,amount,limit_price=None, stop_price=None):
            '''
            Places an order for the specified security of the specified number of shares. Order type is inferred from the parameters used. If only sid and amount are used as parameters, the order is placed as a market order.
            Parameters
            sid: A security object.
            amount: The integer amount of shares. Positive means buy, negative means sell.
            limit_price: (optional) The price at which the limit order becomes active. If used with stop_price, the price where the limit order becomes active after stop_price is reached.
            stop_price: (optional) The price at which the order converts to a market order. If used with limit_price, the price where the order converts to a limit order.
            Returns
            An order id.
            '''
            if sid is Security:
                security = sid
            else:
                security = this.context.framework.allSecurities[sid]
            #log.info("{0} ordering {1}".format(security.qsec,amount))
            order(security.qsec,amount,limit_price,stop_price)
            pass

        def order_percent(self, sid, percent, limit_price=None, stop_price=None):
            """
            Place an order in the specified security corresponding to the given
            percent of the current portfolio value.

            Note that percent must expressed as a decimal (0.50 means 50\%).
            """
            value = self.context.portfolio.portfolio_value * percent
            return self.order_value(sid, value, limit_price, stop_price)

        def order_target(self, sid, target, limit_price=None, stop_price=None):
            """
            Place an order to adjust a position to a target number of shares. If
            the position doesn't already exist, this is equivalent to placing a new
            order. If the position does exist, this is equivalent to placing an
            order for the difference between the target number of shares and the
            current number of shares.
            """
            if sid in self.context.portfolio.positions:
                current_position = self.context.portfolio.positions[sid].amount
                req_shares = target - current_position
                return self.order(sid, req_shares, limit_price, stop_price)
            else:
                return self.order(sid, target, limit_price, stop_price)

        def order_target_value(self, sid, target, limit_price=None,
                               stop_price=None):
            """
            Place an order to adjust a position to a target value. If
            the position doesn't already exist, this is equivalent to placing a new
            order. If the position does exist, this is equivalent to placing an
            order for the difference between the target value and the
            current value.
            """
            if sid in self.context.portfolio.positions:
                current_position = self.context.portfolio.positions[sid].amount
                current_price = self.context.portfolio.positions[sid].last_sale_price
                current_value = current_position * current_price
                req_value = target - current_value
                return self.order_value(sid, req_value, limit_price, stop_price)
            else:
                return self.order_value(sid, target, limit_price, stop_price)

        def order_target_percent(self, sid, target, limit_price=None,
                                 stop_price=None):
            """
            Place an order to adjust a position to a target percent of the
            current portfolio value. If the position doesn't already exist, this is
            equivalent to placing a new order. If the position does exist, this is
            equivalent to placing an order for the difference between the target
            percent and the current percent.

            Note that target must expressed as a decimal (0.50 means 50\%).
            """
            if sid in self.context.portfolio.positions:
                current_position = self.context.portfolio.positions[sid].amount
                current_price = self.context.portfolio.positions[sid].last_sale_price
                current_value = current_position * current_price
            else:
                current_value = 0
            target_value = self.context.portfolio.portfolio_value * target

            req_value = target_value - current_value
            return self.order_value(sid, req_value, limit_price, stop_price)

        pass

    class _TradingAlgorithm_ZiplineShim(zipline.TradingAlgorithm):
        '''auto-generates a context to use'''
        def initialize(this):
            #delay initialize until start of first handle-data, so our
            #portfolio object is available
            #this.__isInitialized = False;
            this.context = Shims.Context()
            this.context.tradingAlgorithm = this            
            #this.context.portfolio = this.portfolio
            pass

        def handle_data(this,data):      
            this.context.portfolio = this.portfolio
            #if not this.__isInitialized:
            #    this.__isInitialized=True
            #    this.context.portfolio=this.portfolio
                
            this.context.framework._update_start(data)
            pass
        pass

class FrameHistory:
    def __init__(this,parent,framework):
        this.parent = parent
        this.framework = framework
        this.state=[]
        this.isActive = this.parent.isActive
        assert(this.framework.simFrame == this.parent.simFrame)
        
        this.initialize()
    
    def initialize(this):
        '''overridable'''
        pass

    def constructFrameState(this,data):
        '''override and return the frame state, this will be prepended to history'''        
        pass

    def update(this,data):
        if not this.isActive:
            return

        maxHistoryFrames = this.framework.maxHistoryFrames

        currentState = this.constructFrameState(data)
        
        currentState.datetime = this.framework.get_datetime()
        currentState.simFrame = this.framework.simFrame

        this.state.insert(0,currentState)
        this.state[0:maxHistoryFrames]


class Position:
    '''
    The position object represents a current open position, and is contained inside the positions dictionary. 
    For example, if you had an open AAPL position, you'd access it using context.portfolio.positions[sid(24)]. 
    The position object has the following properties:
        amount = 0 #Integer: Whole number of shares in this position.
        cost_basis = 0.0 #Float: The volume-weighted average price paid per share in this position.
        last_sale_price = 0.0 #Float: Price at last sale of this security.
        sid = 0 #Integer: The ID of the security.
    '''
    def __init__(this):
        this.amount = 0 #Integer: Whole number of shares in this position.
        this.cost_basis = 0.0 #Float: The volume-weighted average price paid per share in this position.
        this.last_sale_price = 0.0 #Float: Price at last sale of this security.
        this.sid = 0 #Integer: The ID of the security.

class PartialPosition:
    '''allows multiple independent positions per security, 
    each using a fixed percentage of the current portfolio value'''

    def __init__(this, security, strategyName):            
        this.security = security
        this.strategyName = strategyName
        this.lastOrderId = 0
        this.lastStopOrderId = 0
        this.currentCapitalSharePercent = 0.0
        this.currentShares = 0
        #this is editable
        this.targetCapitalSharePercent = 0.0

    def processOrder(this, rebalanceThreshholdPercent=0.05):
        ''' set rebalanceThreshholdPercent to zero (0.0) to cause the position to readjust even if the targetPercentage doesn't change.   this is useful for reinvesting divideds / etc
        but is set to 0.02 (2 percent) so we don't spam orders '''

        this.currentCapitalSharePercent = this.targetCapitalSharePercent       

        #determine value of percent
        targetSharesValue = this.security.framework.context.portfolio.portfolio_value * this.currentCapitalSharePercent
        targetSharesTotal = int(math.copysign(math.floor(abs(targetSharesValue / this.security.state[0].close_price)),targetSharesValue))
        
        targetSharesDelta = targetSharesTotal - this.currentShares

        if targetSharesTotal != 0:
            if targetSharesDelta / (targetSharesTotal * 1.0) < rebalanceThreshholdPercent:
                #our position change was too small so we skip rebalancing
                return

        if(abs(targetSharesDelta) >= 1): #can not perform an order on less than 1 share 
            this.security.framework.logger.info("{0} order {1} : {2} + {3} => {4} shares".format(this.strategyName,this.security.qsec.symbol, this.currentShares, targetSharesDelta, targetSharesTotal ))          
            this.lastOrderId = this.security.framework.tradingAlgorithm.order(this.security.sid,targetSharesDelta)
            this.currentShares = targetSharesTotal

class Security:
    isDebug = False


    class QSecurity:
        '''
        Quantopian internal security object
        If you have a reference to a security object, there are several properties that might be useful:
            sid = 0 #Integer: The id of this security.
            symbol = "" #String: The ticker symbol of this security.
            security_name = "" #String: The full name of this security.
            security_start_date = datetime.datetime() #Datetime: The date when this security first started trading.
            security_end_date = datetime.datetime() #Datetime: The date when this security stopped trading (= yesterday for securities that are trading normally, because that's the last day for which we have historical price data).
        '''
        def __init__(this):
            this.sid = 0 #Integer: The id of this security.
            this.symbol = "" #String: The ticker symbol of this security.
            this.security_name = "" #String: The full name of this security.
            this.security_start_date = datetime.datetime(1990,1,1) #Datetime: The date when this security first started trading.
            this.security_end_date = datetime.datetime(1990,1,1) #Datetime: The date when this security stopped trading (= yesterday for
                                                                 #securities that are trading normally, because that's the last day for which
                                                                 #we have historical price data).
    
    

    def __init__(this,sid, framework):
        this.sid = sid  
        this.isActive = False
        #this.qsec=Security.QSecurity()
        #this.qsec=None
        this.framework = framework
        this.security_start_date = datetime.datetime.utcfromtimestamp(0)
        this.security_end_date = datetime.datetime.utcfromtimestamp(0)
        this.simFrame = -1
        this.security_start_price = 0.0
        this.security_end_price = 0.0
        this.partialPositions = {}
        this.daily_open_price = [0.0]
        this.daily_close_price = [0.0]
        
        
    def getCurrentPosition(this):
        if this.simFrame == -1:
            return Position()
        return this.framework.context.portfolio.positions[this.qsec]

    def update(this,qsec, data):
        '''qsec is only given when it's in scope, and it can actually change each timestep 
        what it does:
        - construct new state for this frame
        - update qsec to most recent (if any)
        '''
        #update our tickcounter, mostly for debug
        this.simFrame = this.framework.simFrame
        assert(this.simFrame >= 0)

        
        
        #update qsec to most recent (if any)
        this.qsec = qsec
        if qsec:
            this.isActive = True
            assert(qsec.sid == this.sid)            
            
            if this.security_start_price == 0.0:
                this.security_start_price = data[this.sid].close_price
            this.security_end_price = data[this.sid].close_price

            this.security_start_date = qsec.security_start_date
            this.security_end_date = qsec.security_end_date
        else:
            this.isActive = False

        try:
            this.daily_close_price = this.framework.daily_close_price[this.qsec]
            this.daily_open_price = this.framework.daily_open_price[this.qsec]
        except:
            this.daily_close_price = []
            this.daily_open_price = []

        if len(this.daily_close_price) == 0 or len(this.daily_open_price) == 0:
            this.isActive = False

    def update_orders_phase4(this,data):
        '''handles processing of partial positions'''
        for name, partialPosition in this.partialPositions.items():
           partialPosition.processOrder()



class FrameworkBase():
    def __init__(this, context, isOffline, maxHistoryFrames=365):
        this.maxHistoryFrames = maxHistoryFrames
        this.__isFirstTimestepRun = False
        this.isOffline = isOffline
        this.context = context
        this.tradingAlgorithm = Shims._TradingAlgorithm_QuantopianShim() #prepopulate to allow intelisence
        this.tradingAlgorithm = context.tradingAlgorithm
        this.simFrame = -1 #the current timestep of the simulation
        
        this.allSecurities = {} #dictionary of all securities, including those not targeted
        this.activeSecurities = {}

        this.thisFrameDay = 0
        this.lastFrameDay = 0

        if is_offline_Zipline:
            this.logger = Shims._Logger(this)
        else:
            this.logger = log


        #for storing quantopian history
        this.daily_close_price = pandas.DataFrame()
        this.daily_open_price = pandas.DataFrame()
        

        pass
    
    def initialize(this):
        #do init here
        this.init_internal()
        pass

    def init_internal(this):
        '''override this to do your init'''
        pass


    def initialize_first_update(this,data):
        '''called the first timestep, before update'''
        pass

    def _update_start(this,data):
        '''invoked by the tradingAlgorithm shim every update.  internally we will call abstract_update_timestep_handle_data()
        Override this, but call the super first!!!!
        '''

        #frame updates
        #this.data = data

        this.simFrame+=1        
        
        this.lastFrameDay = this.thisFrameDay
        this.thisFrameDay = this.get_datetime().day
        
        #supdating our history once per day
        if(this.thisFrameDay != this.lastFrameDay):
            #only update this once per day, hopefully improving performance...
            this.daily_close_price = history(bar_count=180, frequency='1d', field='close_price')
            this.daily_open_price = history(bar_count=180, frequency='1d', field='open_price')

        this.__updateSecurities(data)
        

        if not this.__isFirstTimestepRun:
            this.__isFirstTimestepRun = True
            this.initialize_first_update(data)

        this.update(data)
        pass

    def update(this,data):
        '''override and update your usercode here'''
        pass

    def __updateSecurities(this,data):
        '''get all qsecs from data, then update the targetedSecurities accordingly'''

        #convert our data into a dictionary
        currentQSecs = {}
        newQSecs = {}
        for qsec in data:
            if not this.isOffline:
                #if online, qsec is a securities object
                sid = qsec.sid                
            else:
                #if offline (zipline), qsec is a string ex: "SPY"
                sid = qsec
                qsec = data[qsec]
            currentQSecs[sid] = qsec
            #determine new securities found in data
            if not this.allSecurities.has_key(sid):
                newQSecs[sid] = qsec


        #construct new Security objects for our newQSecs
        for sid, qsec in newQSecs.items():            
            assert(not this.allSecurities.has_key(sid))

            this.allSecurities[sid] = this.GetOrCreateSecurity(sid, qsec, data)

        newQSecs.clear()


        #update all security objects, giving a null qsec if one doesn't exist
        #in our data dictionary
        for sid, security in this.allSecurities.items():
            qsec = currentQSecs.get(sid)
            security.update(qsec, data)

        ## determine active securities set.
        this.activeSecurities.clear()
        for sid,security in this.allSecurities.items():
            if not security.isActive:
                continue
            this.activeSecurities[sid] = security
            pass

        pass

    def _initializeSecurity(this,security,data):
        '''override to do custom init logic on each security. 
        if you wish to use your own security, return it (it will replace the existing)'''
        pass       
             
    #def GetOrCreateSecuritySecurities(this,qsecArray):
    #    '''pass in an array of quantopian sec (ex:  [sid(24),sid(3113)]) 
    #    and returns an array of unique security objects wrapping them.   duplicate sids are ignored'''
    #    securities = {}
    #    for qsec in qsecArray:
    #        sid = qsec.sid
    #        securities[sid] = this.GetOrCreateSecurity(qsec)
    #        pass
    #    return securities.values()
    #    pass
    def GetOrCreateSecurity(this, sid, qsec, data):
        '''pass in a quantopian sec (ex:  sid(24)) and returns our security object wrapping it
        if the security object
        '''
        

        if this.allSecurities.has_key(sid):
            return this.allSecurities[sid]

        #does not exist, have to create
        newSecurity = Security(sid,this)
        #new, so do our framework's custom init logic on this security
        maybeNewSec = this._initializeSecurity(newSecurity,data)
        if maybeNewSec is not None:
            #framework replaced newSec with a different sec
            newSecurity = maybeNewSec
                
        this.allSecurities[sid] = newSecurity
        
        return newSecurity
        pass


    def get_datetime(this):
        #if is_offline_Zipline:
        #    if len(this.allSecurities) == 0:
        #        return datetime.datetime.fromtimestamp(0,pytz.UTC)
        #    else:
        #        assert(False,"need to fix this to return something valid.  all securities isn't good enough.  probably search for first active")
        #        return this.allSecurities.values()[0].datetime
        #else:
        #    return get_datetime()
        #pass
        return get_datetime()
#entrypoints


def initalize_zipline():
    '''initialize method run when using zipline'''
    
    tradingAlgorithm = Shims._TradingAlgorithm_ZiplineShim()
    context = tradingAlgorithm.context
    context.framework = constructFramework(context,True)
    context.framework.initialize()    
    tradingAlgorithm.run(context.framework._offlineZiplineData)
    pass

def handle_data(context=Shims.Context(),data=pandas.DataFrame()):    
    '''update method run every timestep on quantopian'''
    if context.firstFrame:
        #'''init on our first frame'''
        context.firstFrame = False
        context.tradingAlgorithm = Shims._TradingAlgorithm_QuantopianShim()
        context.tradingAlgorithm.context = context
        context.framework = constructFramework(context,False)
        context.framework.initialize()
    
    context.framework._update_start(data)
    
    pass

def initialize(context=Shims.Context()):
    '''initialize method used when running on quantopian'''
    context.firstFrame = True 

    context.sec = sid(19656);
    log.info(context.sec)

    ########## SET UNIVERSE
    #if you need set universe, do it here (note that doing this slows the algo
    #considerably, seems frozen)
    #set_universe(universe.DollarVolumeUniverse(floor_percentile=99.5,ceiling_percentile=100.0))

    ########## COMMISSION
    #use top to decrease uncertainty when testing algorithms
    #set_commission(commission.PerShare(cost=0.0))
    set_commission(commission.PerShare(cost=0.005, min_trade_cost=1.00)) #IB fixed commission model
    
    ########## SLIPPAGE
    #use top to decrease uncertainty when testing algorithms
    #set_slippage(slippage.FixedSlippage(spread=0.00))
    #set_slippage(slippage.FixedSlippage(spread=0.01))  
    set_slippage(WorstSpreadSlippage())

##############  CROSS PLATFORM USERCODE BELOW.  EDIT BELOW THIS LINE
##############  CROSS PLATFORM USERCODE BELOW.  EDIT BELOW THIS LINE
##############  CROSS PLATFORM USERCODE BELOW.  EDIT BELOW THIS LINE
class StandardTechnicalIndicators(FrameHistory):

    class State:
        def __init__(this,parent,data):
            this.parent = parent
            #preset for proper intelisence
            this.datetime = datetime.datetime.now()
            this.open_price = 0.0
            this.close_price = 0.0
            this.high = 0.0
            this.low = 0.0
            this.volume = 0

            this.mavg3 = 0.0
            this.mavg7 = 0.0  
            this.mavg15 = 0.0
            this.mavg30 = 0.0    
            this.mavg45 = 0.0
            this.mavg60 = 0.0

            this.stddev3 = 0.0
            this.stddev7 = 0.0
            this.stddev15 = 0.0
            this.stddev30 = 0.0
            this.stddev45 = 0.0
            this.stddev60 = 0.0

            this.datetime = data[this.parent.qsec].datetime
            this.open_price = data[this.parent.qsec].open_price
            this.close_price = data[this.parent.qsec].close_price
            this.high = data[this.parent.qsec].high
            this.low = data[this.parent.qsec].low
            this.volume = data[this.parent.qsec].volume

            this.mavg3 = data[this.parent.qsec].mavg(3)
            this.mavg7 = data[this.parent.qsec].mavg(7)        
            this.mavg15 = data[this.parent.qsec].mavg(15)
            this.mavg30 = data[this.parent.qsec].mavg(30)        
            this.mavg45 = data[this.parent.qsec].mavg(45)
            this.mavg60 = data[this.parent.qsec].mavg(60)

            this.stddev3 = data[this.parent.qsec].stddev(3)
            this.stddev7 = data[this.parent.qsec].stddev(7)        
            this.stddev15 = data[this.parent.qsec].stddev(15)
            this.stddev30 = data[this.parent.qsec].stddev(30)        
            this.stddev45 = data[this.parent.qsec].stddev(45)
            this.stddev60 = data[this.parent.qsec].stddev(60)

            try:                
                this.returns = data[this.parent.qsec].returns()
            except:
                this.framework.logger.error("{0} unable to obtain returns()  setting returns to zero  open={1}.  close = {2}".format(this.parent.qsec, this.open_price, this.close_price))
                this.returns = 0.0

    def constructFrameState(this,data):
        currentState = StandardTechnicalIndicators.State(this.parent,data)
        return currentState
        

#class FollowMarketStrategy(FrameStateBase):
#    def initialize(this, data):
#        #partialPositions
#        this.parialPosition = this.parent.partialPositions["followMarketStrategy"]

#        security = this.parent
        
#        #simple "follow market" example
        
#        if security.state[0].close_price < security.standardIndicators[0].mavg7 and security.standardIndicators[0].mavg7 < security.standardIndicators[0].mavg30:
#            this.parialPosition.targetCapitalSharePercent = 1.0
#        elif security.state[0].close_price > security.standardIndicators[0].mavg7 and security.standardIndicators[0].mavg7 > security.standardIndicators[0].mavg30:
#            this.parialPosition.targetCapitalSharePercent = -1.0
#        else:
#            this.parialPosition.targetCapitalSharePercent = 0.0

#        pass

#class FollowPriorDayStrategy(FrameStateBase):
#    def initialize(this, data):
#        #partialPositions
#        this.parialPosition = this.parent.partialPositions["followPriorDayStrategy"]

#        security = this.parent
        
#        if len(security.daily_close_price) < 2:
#            this.framework.logger.warn("security has invalid days {0}".format(security.qsec))
#            return

#        #simple "follow prior day" example
#        wasYesterdayUp = security.daily_close_price[-1] > security.daily_close_price[-2]
#        if wasYesterdayUp:
#            #long
#            this.parialPosition.targetCapitalSharePercent = 1.0
#        else:
#            #short
#            this.parialPosition.targetCapitalSharePercent = -1.0
#        pass


class ExampleAlgo(FrameworkBase):

    #def init_internal(this):
    #    pass


    #def initialize_first_update(this, data):
    #    pass

    def update(this, data):
        ##PHASE 1: do any housekeeping during updates here
        #no-op
        return

        ##PHASE 2: update technical indicators for ALL active securities (targeted or not)
        for sid,security in this.activeSecurities.items():
            this.__update_technicalIndicators(security,data)
       

        #for sid,security in this.targetedSecurities.items():
        #    if not security.isActive:
        #        continue
        #    #PHASE 3: update algorithms for targetedSecurities
        #    this.__update_algorithms(security,data)

           
        #for sid,security in this.targetedSecurities.items():
        #    if not security.isActive:
        #        continue
        #    ##PHASE 4: process orders for targetedSecurities
        #    this.__update_orders(security,data)
        #record(port_value = this.context.portfolio.portfolio_value, pos_value = this.context.portfolio.positions_value , cash = this.context.portfolio.cash)

    def _initializeSecurity(this,security,data):
        '''do our framework's custom init logic on this security'''
        security.standardIndicators = StandardTechnicalIndicators(security,this)
        
        #security.followMarketStrategy = [] #history for tthis strategy
        #security.partialPositions["followMarketStrategy"] = PartialPosition(security, "followMarketStrategy") 

        #security.followPriorDayStrategy = [] #history for tthis strategy
        #security.partialPositions["followPriorDayStrategy"] = PartialPosition(security, "followPriorDayStrategy")

        pass

    def __update_technicalIndicators(this,security,data):
        '''##PHASE 2: update technical indicators for ALL active securities found'''
        security.standardIndicators.update(data)
        pass

    def __update_algorithms(this,security,data):
        '''#PHASE 3: update algorithms for targetedSecurities'''
        
        #followMarketStrategy = FollowMarketStrategy(security,this)
        #followMarketStrategy.initializeAndPrepend(security.followMarketStrategy,data)
        
        #followPriorDayStrategy = FollowPriorDayStrategy(security,this)
        #followPriorDayStrategy.initializeAndPrepend(security.followPriorDayStrategy,data)

        pass
    def __update_orders(this,security,data):    
        '''##PHASE 4: process orders for targetedSecurities     '''  

        security.update_orders_phase4(data)

class Study:
    def __init__(this,framework):
        this.framework = framework
    def initialize(this,data):
        pass
    def update_start(this,data):
        pass
    def update_securities(this,data):
        pass
    def update_orders(this,data):
        pass
    def update_end(this,data):
        pass

##############  CONFIGURATION BELOW
def constructFramework(context,isOffline):
    '''factory method to return your custom framework/trading algo'''
    return ExampleAlgo(context,isOffline)

############## OFLINE RUNNER BELOW.  EDIT ABOVE THIS LINE
if __name__ == '__main__':  
    is_offline_Zipline = True
    initalize_zipline() #obsolete, this framework doesn't work with zipline anymore
