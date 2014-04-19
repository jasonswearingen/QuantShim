# -*- coding: utf-8 -*-  
"""
TL;DR:  
1) jump to the end of this file
2) replace/extend "ExampleFramework" (around line 800)
3) copy/paste this file to quantopian 
4) backtest
-------------

@summary: An intraday algorithmic trading framework for use with quantopian.com   
Primary use is to support multiple algorithms cooperating

@license: gpl v3

@author: JasonS@Novaleaf.com  https://PhantomJsCloud.com

@disclaimer:  I'm not a fan of python so sorry that this isn't PEP compliant.


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
    additionally, supports 'VolumeShareSlippage' functionality, which further biases price/volume
    IMPORTANT NOTE: only meant for intraday (minute data) use.  using with daily data will cause unrealisticly poor performance.'''
    def __init__(this, volume_limit=.25, price_impact=0.1):
        this.volume_limit = volume_limit
        this.price_impact = price_impact
        pass
    def __processVolumeShareSlippage(self,event,order, targetPrice):
        '''coppied implementation from VolumeShareSlippage.process_order(), found here: https://github.com/quantopian/zipline/blob/4860a966b3a3102fa80d43f393155e53015cc349/zipline/finance/slippage.py
        modification:  we return the final (price,volume) tuple for our main .process_order() to use, instead of executing the order
        RETURNS: final (price,volume) tuple'''
        ######## 
        max_volume = self.volume_limit * event.volume

        # price impact accounts for the total volume of transactions
        # created against the current minute bar
        remaining_volume = max_volume - self.volume_for_bar
        if remaining_volume < 1:
            # we can't fill any more transactions
            return (0.0,0)
        # the current order amount will be the min of the
        # volume available in the bar or the open amount.
        cur_volume = int(min(remaining_volume, abs(order.open_amount)))

        if cur_volume < 1:
            return (0.0,0)

        # tally the current amount into our total amount ordered.
        # total amount will be used to calculate price impact
        total_volume = self.volume_for_bar + cur_volume

        volume_share = min(total_volume / event.volume,
                           self.volume_limit)

        simulated_impact = volume_share ** 2 \
            * math.copysign(self.price_impact, order.direction) \
            * targetPrice
        #return create_transaction(
        #    event,
        #    order,
        #    # In the future, we may want to change the next line
        #    # for limit pricing
        #    event.price + simulated_impact,
        #    math.copysign(cur_volume, order.direction)
        return (targetPrice + simulated_impact,int(math.copysign(cur_volume, order.direction)))

    def process_order(this,trade_bar,order):
        
        
        if order.amount < 0:
            targetPrice = trade_bar.low
        else:
            targetPrice = trade_bar.high
        
        price, volume = this.__processVolumeShareSlippage(trade_bar,order,targetPrice)
        priceSlippage = trade_bar.close_price - price   
        volumeSlippage = order.amount - volume    

        if price == 0.0 or volume==0:
            return

        #log.info(price)        
        log.info("{4} ORDER_COMMITTED: {0} shares {1} @ {2} \n\t  v={9} o={5} h={6} l={7} c={8} \t (WorstSpreadSlippage: vol= -{10} price= {3:.2f})"
                    .format(volume,trade_bar.sid.symbol,price,priceSlippage,get_datetime(),trade_bar.open_price, trade_bar.high, trade_bar.low, trade_bar.close_price, trade_bar.volume,volumeSlippage ))
        
        return slippage.create_transaction(
                                            trade_bar,
                                            order,
                                            price,
                                            order.amount
                                            )

class Shims():
    '''SHIM OF QUANTOPIAN INTERNAL REPRESENTATION.  here for intelisence only.  you SHOULD NOT actually instantiate these.'''
    
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
            print("{0} !!ERROR!! {1}".format(this.framework._getDatetime(),message))             
            pass
        def info(this, message):
            print("{0} info {1}".format(this.framework._getDatetime(),message))            
            pass
        def warn(this, message):   
            print("{0} WARN {1}".format(this.framework._getDatetime(),message))          
            pass
        def debug(this, message):  
            print("{0} debug {1}".format(this.framework._getDatetime(),message))                           
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
                
            this.context.framework._update(data)
            pass
        pass

class FrameHistory:
    def __init__(this,parent,framework):
        this.parent = parent
        this.framework = framework
        this.state=[]
        this.isActive = this.parent.isActive
        #assert(this.framework.simFrame == this.parent.simFrame, "parent frame does not match")
        
        this.initialize()
    
    def initialize(this):
        '''overridable'''
        pass

    def constructFrameState(this,data):
        '''override and return the frame state, this will be prepended to history'''   
        log.error("FrameHistory.constructFrameState() invoked.  You should override this method.")             
        pass

    def update(this,data):
        this.isActive = this.parent.isActive
        if not this.isActive:
            return

        maxHistoryFrames = this.framework.maxHistoryFrames

        currentState = this.constructFrameState(data)
        
        currentState.datetime = this.framework._getDatetime()
        currentState.simFrame = this.framework.simFrame

        this.state.insert(0,currentState)
        this.state[0:maxHistoryFrames]



class StrategyPosition:
    '''allows two or more stratgies to controll their own positions (orders) for securities they care about, 
    without interfering with the orders of other strategies.

    To use:   each strategy should set security.myStrategyPositon.targetCapitalSharePercent, which is a percentage of your entire portfolio's value
    then execute the order (and/or rebalance) by invoking security.myStrategyPosition.processOrder()
    '''

    def __init__(this, security, strategyName):            
        this.security = security
        this.strategyName = strategyName
        this.lastOrderId = 0
        this.lastStopOrderId = 0
        this.currentCapitalSharePercent = 0.0
        this.currentShares = 0
        #this is editable
        this.targetCapitalSharePercent = 0.0

    def processOrder(this, data, rebalanceThreshholdPercent=0.05):
        ''' set rebalanceThreshholdPercent to zero (0.0) to cause the position to readjust even if the targetPercentage doesn't change.   this is useful for reinvesting divideds / etc
        but is set to 0.02 (2 percent) so we don't spam orders '''
        
        this.currentCapitalSharePercent = this.targetCapitalSharePercent       

        #determine value of percent
        targetSharesValue = this.security.framework.context.portfolio.portfolio_value * this.currentCapitalSharePercent
        targetSharesTotal = int(math.copysign(math.floor(abs(targetSharesValue / data[this.security.qsec].close_price)),targetSharesValue))
        
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
        this.framework = framework
        this.security_start_date = datetime.datetime.utcfromtimestamp(0)
        this.security_end_date = datetime.datetime.utcfromtimestamp(0)
        this.simFrame = -1
        this.security_start_price = 0.0
        this.security_end_price = 0.0
        this.daily_open_price = [0.0]
        this.daily_close_price = [0.0]
        
        
    def getCurrentPosition(this):
        if this.simFrame == -1:
            return Shims.Position()
        return this.framework.context.portfolio.positions[this.qsec]

    def update(this,qsec, data):
        '''qsec is only given when it's in scope, and it can actually change each timestep 
        what it does:
        - construct new state for this frame
        - update qsec to most recent (if any)
        '''
        #update our tickcounter, mostly for debug
        this.simFrame = this.framework.simFrame
        #assert(this.simFrame >= 0,"security.update() frame not set")

        
        
        #update qsec to most recent (if any)
        this.qsec = qsec
        if qsec:
            this.isActive = True
            #assert(qsec.sid == this.sid,"security.update() sids do not match")            
            
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
    
    def _initialize(this):
        '''starts initialiation of the framework
        do not override this, or any other method starting with an underscore.
        methods without an underscore prefix can and should be overridden.'''
        #do init here
        this.initialize()
        pass

    def initialize(this):
        '''override this to do your init'''
        log.error("You should override FrameworkBase.initialize()")
        pass


    def initializeFirstUpdate(this,data):
        '''override this.  called the first timestep, before update.  
        provides access to the 'data' object which normal .initialize() does not'''
        log.error("You should override FrameworkBase.initializeFirstUpdate()")
        pass

    def _update(this,data):
        '''invoked by the tradingAlgorithm shim every update.  internally we will call abstract_update_timestep_handle_data()
        DO NOT OVERRIDE THIS OR ANY METHODS STARTING WITH AN UNDERSCORE
        override methods without underscores.
        '''

        #frame updates
        #this.data = data

        this.simFrame+=1        
        
        this.lastFrameDay = this.thisFrameDay
        this.thisFrameDay = this._getDatetime().day
        
        #supdating our history once per day
        if(this.thisFrameDay != this.lastFrameDay):
            #only update this once per day, hopefully improving performance...
            this.daily_close_price = history(bar_count=180, frequency='1d', field='close_price')
            this.daily_open_price = history(bar_count=180, frequency='1d', field='open_price')

        this.__updateSecurities(data)
        

        if not this.__isFirstTimestepRun:
            this.__isFirstTimestepRun = True
            this.initializeFirstUpdate(data)

        this.update(data)
        pass

    def update(this,data):
        '''override and update your usercode here'''
        log.error("You should override FrameworkBase.update()")
        pass

    def __updateSecurities(this,data):
        '''get all qsecs from data, then update the targetedSecurities accordingly'''
        #log.debug("FrameworkBase.__updateSecurities() start.   allSecLength={0}".format(len(this.allSecurities)))
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
            
            #log.debug("FrameworkBase.__updateSecurities() first loop, found {0}, sid={1}.   exists={2}".format(qsec, sid,this.allSecurities.has_key(sid) ))

            currentQSecs[sid] = qsec
            #determine new securities found in data
            if not this.allSecurities.has_key(sid):
                log.debug("FrameworkBase.__updateSecurities() new security detected.  will construct our security object for it: {0}".format(qsec))
                newQSecs[sid] = qsec


        #construct new Security objects for our newQSecs
        for sid, qsec in newQSecs.items():            
            #assert(not this.allSecurities.has_key(sid),"frameworkBase.updateSecurities key does not exist")
            #log.debug("FrameworkBase.__updateSecurities() new security found {0}".format(qsec))
            this.allSecurities[sid] = this._getOrCreateSecurity(sid, qsec)

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
                #log.debug("FrameworkBase.__updateSecurities() NOT ACTIVE {0}".format(security.qsec))
                continue
            #log.debug("FrameworkBase.__updateSecurities() ACTIVE {0}".format(security.qsec))
            this.activeSecurities[sid] = security
            pass

        pass

    def initializeSecurity(this,security):
        '''override to do custom init logic on each security. 
        if you wish to use your own security, return it (it will replace the existing)'''
        log.error("You should override FrameworkBase.initializeSecurity()")
        pass       
             
    def _getOrCreateSecurities(this,qsecArray):
        '''pass in an array of quantopian sid/sec tuples  (ex:  [(24,sid(24)),(3113,sid(3113))]) 
        and returns an array of unique security objects wrapping them.   duplicate sids are ignored'''

        securities = {}

        for sid, qsec in qsecArray:
            #sid = qsec.sid
            securities[sid] = this._getOrCreateSecurity(sid,qsec)
            pass

        return securities.values()

    def _getOrCreateSecurity(this, sid, qsec):
        '''pass in a quantopian sec (ex:  sid(24)) and returns our security object wrapping it
        if the security object
        '''
        

        if this.allSecurities.has_key(sid):
            return this.allSecurities[sid]

        #does not exist, have to create
        newSecurity = Security(sid,this)
        #new, so do our framework's custom init logic on this security
        maybeNewSec = this.initializeSecurity(newSecurity)
        if maybeNewSec is not None:
            #framework replaced newSec with a different sec
            newSecurity = maybeNewSec
                
        this.allSecurities[sid] = newSecurity
        
        return newSecurity
        pass


    def _getDatetime(this):
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
    context.framework._initialize()    
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
        context.framework._initialize()
    
    context.framework._update(data)
    
    pass

def initialize(context=Shims.Context()):
    '''initialize method used when running on quantopian'''
    context.firstFrame = True 
    
    ########## SET UNIVERSE
    #if you need set universe, do it here (note that doing this slows the algo considerably)
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
    '''common technical indicators that we plan to use for any/all strategies
    feel free to extend this, or use as a reference for constructing specialized technical indicators'''
    class State:
        '''State recorded for each frame (minute).  number of frames history we store is determined by framework.maxHistoryFrames'''
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
        #log.debug("StandardTechnicalIndicators.constructFrameState")
        currentState = StandardTechnicalIndicators.State(this.parent,data)
        return currentState

    
class QuantopianRealMoney9SectorStrategy:
    '''this example strategy implements the trading algo that the quantopian principles are using for real money trading.
    see here: https://www.quantopian.com/posts/rebalance-algo-9-sector-etfs '''
    def __init__(this,framework):
        # This initialize function sets any data or variables that you'll use in your
        # algorithm. You'll also want to define any parameters or values you're going to use.
        this.framework = framework
        
        # In our example, we're looking at 9 sector ETFs.  
        #HACK:  due to quantopian sandbox stupidity, need to add the sid explicitly.  see https://www.quantopian.com/posts/build-error-annoyances-nonexistent-property-sid
        this.secs = this.framework._getOrCreateSecurities([ 
            (19662,sid(19662)),  # XLY Consumer Discrectionary SPDR Fund   
            (19656,sid(19656)),  # XLF Financial SPDR Fund  
            (19658,sid(19658)),  # XLK Technology SPDR Fund  
            (19655,sid(19655)),  # XLE Energy SPDR Fund  
            (19661,sid(19661)),  # XLV Health Care SPRD Fund  
            (19657,sid(19657)),  # XLI Industrial SPDR Fund  
            (19659,sid(19659)),  # XLP Consumer Staples SPDR Fund   
            (19654,sid(19654)),  # XLB Materials SPDR Fund  
            (19660,sid(19660)) # XLU Utilities SPRD Fund)
            ] )

        # Change this variable if you want to rebalance less frequently
        this.rebalance_days = 5

        # These other variables are used in the algorithm for leverage, trade time, etc.
        this.today = None
        this.weights = 0.99/len(this.secs)    
        this.leverage=2

        #add StrategyPositions to each of our strategy's securities so as to not interfere with other strategies
        for sec in this.secs:
            sec.quantopianStrategyPosition = StrategyPosition(sec,"quantopianRealMoney9SectorStrategy")
            
    def update(this,data):
        # Get the current exchange time, in the exchange timezone 
        exchange_time = pandas.Timestamp(get_datetime()).tz_convert('US/Eastern')
        if  this.today == None or exchange_time >= this.today + datetime.timedelta(days=this.rebalance_days):
            #new day, open positions
            this.today = exchange_time
        
            #determine order amount per security
            for sec in this.secs:
                sec.quantopianStrategyPosition.targetCapitalSharePercent = this.weights * this.leverage  # order_target_percent(sec, context.weights * context.leverage, limit_price=None, stop_price=None)

            #execute orders / rebalancing
            for sec in this.secs:
                sec.quantopianStrategyPosition.processOrder(data, rebalanceThreshholdPercent=0.0)
            pass

class ExampleFramework(FrameworkBase):
    '''Example framework for you to extend, or use as reference.   
    this example populates standardIndicators for all securities (including history), 
    and executes the following example strategies:  QuantopianRealMoney9SectorStrategy, '''
    def initialize(this):
        '''initialization logic for your framework goes here.
        our naming conventions imply any function starting with an underscore SHOULD NOT be overridden.   
        functions without an underscore can (and should) be overriden.'''
        this.quantopianRealMoney = QuantopianRealMoney9SectorStrategy(this)
        pass

    def initializeFirstUpdate(this, data):
        '''called the first timestep, before update.  
        provides access to the 'data' object which normal .initialize() does not'''
        pass

    def initializeSecurity(this,security):
        '''The QuantShim framework constructs a "Security" object wrapping the quantopian sec  (we call it 'qsec')
        add initialization logic to securities here, such as shown by our adding of 'standardIndicators' below
        '''
        #attach standard technical indicators to our security
        security.standardIndicators = StandardTechnicalIndicators(security,this)
        pass

    def update(this, data):
        '''this .update() method is invoked every frame (once per minute interval of quantopian) 
        here is where you hook your strategies, etc logic.  think of this as your '.handle_data' loop'''

        ##PHASE 1: update technical indicators for ALL active securities (targeted or not)
        for sid,security in this.activeSecurities.items():
            #log.debug("ExampleAlgo.update() about to update stdInd {0}, sid={1}".format(security, sid))
            security.standardIndicators.update(data) 
       
        ##PHASE 2: run our strategies
        this.quantopianRealMoney.update(data)

        ##various graphing
        record(port_value = this.context.portfolio.portfolio_value, pos_value = this.context.portfolio.positions_value , cash = this.context.portfolio.cash)

    pass



##############  CONFIGURATION BELOW
def constructFramework(context,isOffline):
    '''factory method to return your custom framework/trading algo'''
    return ExampleFramework(context,isOffline)

############## OBSOLETE OFLINE RUNNER BELOW.  EDIT ABOVE THIS LINE
if __name__ == '__main__':  
    is_offline_Zipline = True
    initalize_zipline() #obsolete, this framework doesn't work with zipline anymore
