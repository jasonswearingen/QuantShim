# -*- coding: utf-8 -*-  
"""
TL;DR:  
1) jump to the end of this file
2) replace/extend "ExampleFramework" (around line 1601)
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
import functools
import collections

import sklearn
import sklearn.naive_bayes
#import sklearn.naive_bayes.BernoulliNB
import sklearn.linear_model
import sklearn.ensemble

import talib




is_offline_Zipline = False

#quantopian shims
class WorstSpreadSlippage(slippage.SlippageModel):
    '''will trade at the worst value of the order minute.  high if long, low if short. 
    additionally, supports 'VolumeShareSlippage' functionality, which further biases price/volume'''
    def __init__(this, volume_limit=.25, price_impact=0.1, ohlcWeighted=False):
        this.volume_limit = volume_limit
        this.price_impact = price_impact
        this.ohlcWeighted = ohlcWeighted
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
        
        #worst spread
        if order.amount < 0:
            targetPrice = trade_bar.low
        else:
            targetPrice = trade_bar.high
        #trade at the open
        #targetPrice = trade_bar.open_price

        if this.ohlcWeighted:
            #midpoint, ohlc weighted
            targetPrice = (targetPrice + trade_bar.open_price + trade_bar.high + trade_bar.low + trade_bar.close_price) / 5
            pass


        price, volume = this.__processVolumeShareSlippage(trade_bar,order,targetPrice)
        priceSlippage = trade_bar.close_price - price   
        volumeSlippage = order.amount - volume    

        if price == 0.0 or volume == 0:
            return

        #logger.info(price)
        logger.info("ORDER_COMMITTED: {0} shares {1} @ {2} \n\t  v={8} o={4} h={5} l={6} c={7} \t (WorstSpreadSlippage: vol= -{9} price= {3:.2f})"
                    .format(volume,trade_bar.sid.symbol,price,priceSlippage, trade_bar.open_price, trade_bar.high, trade_bar.low, trade_bar.close_price, trade_bar.volume,volumeSlippage))
        
        return slippage.create_transaction(trade_bar,
                                            order,
                                            price,
                                            order.amount)

class TradeAtTheOpenSlippageModel_Simple(slippage.SlippageModel):
    def __init__(self, fractionOfOpenCloseRange):
        self.fractionOfOpenCloseRange = fractionOfOpenCloseRange

    def process_order(self, trade_bar, order):
        openPrice = trade_bar.open_price
        closePrice = trade_bar.price
        ocRange = closePrice - openPrice
        ocRange = ocRange * self.fractionOfOpenCloseRange
        targetExecutionPrice = openPrice + ocRange
            
        # Create the transaction using the new price we've calculated.
        return slippage.create_transaction(
            trade_bar,
            order,
            targetExecutionPrice,
            order.amount
        )
        
class TradeAtTheOpenSlippage(slippage.SlippageModel):
    '''will trade at the open, good for daily use, kind of not good otherwise.'''
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
        
        
        #if order.amount < 0:
        #    targetPrice = trade_bar.low
        #else:
        #    targetPrice = trade_bar.high
        targetPrice = trade_bar.open_price

        price, volume = this.__processVolumeShareSlippage(trade_bar,order,targetPrice)
        priceSlippage = trade_bar.close_price - price   
        volumeSlippage = order.amount - volume    

        if price == 0.0 or volume == 0:
            return

        #logger.info(price)
        logger.info("ORDER_COMMITTED: {0} shares {1} @ {2} \n\t  v={8} o={4} h={5} l={6} c={7} \t (TradeAtTheOpenSlippage: vol= -{9} price= {3:.2f})"
                    .format(volume,trade_bar.sid.symbol,price,priceSlippage, trade_bar.open_price, trade_bar.high, trade_bar.low, trade_bar.close_price, trade_bar.volume,volumeSlippage))
        
        return slippage.create_transaction(trade_bar,
                                            order,
                                            price,
                                            order.amount)

    
class CustomSlippage(slippage.SlippageModel):
    ''' allows customizing slippage if desired, though mostly used for logging your order details to the console'''
    def __init__(this, volume_limit=.25, price_impact=0.1, ohlcWeighted=False):
        this.volume_limit = volume_limit
        this.price_impact = price_impact
        this.ohlcWeighted = ohlcWeighted
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

        simulated_impact = volume_share ** 2 * math.copysign(self.price_impact, order.direction) * targetPrice
        #return create_transaction(
        #    event,
        #    order,
        #    # In the future, we may want to change the next line
        #    # for limit pricing
        #    event.price + simulated_impact,
        #    math.copysign(cur_volume, order.direction)
        return (targetPrice + simulated_impact,int(math.copysign(cur_volume, order.direction)))

    def process_order(this,trade_bar,order):
        
        ####worst spread
        #if order.amount < 0:
        #    targetPrice = trade_bar.low
        #else:
        #    targetPrice = trade_bar.high
        ####trade at the open
        #targetPrice = trade_bar.open_price
        ####trade at the close
        targetPrice = trade_bar.close_price

        if this.ohlcWeighted:
            #midpoint, ohlc weighted
            targetPrice = (targetPrice + trade_bar.open_price + trade_bar.high + trade_bar.low + trade_bar.close_price) / 5
            pass


        price, volume = this.__processVolumeShareSlippage(trade_bar,order,targetPrice)
        priceSlippage = trade_bar.close_price - price   
        volumeSlippage = order.amount - volume    

        if price == 0.0 or volume == 0:
            return
        
        
        #construct our pnl once this transaction is comitted (logged below)
        pnl = _g.context.portfolio.pnl + (price * order.amount) - (trade_bar.close_price * order.amount)

        #logger.info(price)
        logger.info("ORDER_COMMITTED: {0} shares {1} @ {2} \n\t  v={8} o={4} h={5} l={6} c={7} \t (Slippage: vol= -{9} price= {3:.2f})\n\tpnl={10}"
                    .format(volume,trade_bar.sid.symbol,price,priceSlippage, trade_bar.open_price, trade_bar.high, trade_bar.low, trade_bar.close_price, trade_bar.volume,volumeSlippage, pnl))
        
        return slippage.create_transaction(trade_bar,
                                            order,
                                            price,
                                            order.amount)

class Logger():
    '''shim for exposing the same logging definitions to visualstudio intelisence'''
    def __init__(this, logErrors=True, logInfos=True, logWarns=True, logDebugs=True):        
        this.__logErrors = logErrors
        this.__logInfos = logInfos
        this.__logWarns = logWarns
        this.__logDebugs = logDebugs
        this.__recordHistory = {}
        this.__lastKnownDay = None
        pass    

    def error(this, message): 
        if not this.__logErrors: return  
        log.error(this.__wrapMessage(message))
        pass
    def info(this, message):
        if not this.__logInfos: return  
        log.info(this.__wrapMessage(message))
        pass
    def warn(this, message):   
        if not this.__logWarns: return  
        log.warn(this.__wrapMessage(message))
        pass
    def debug(this, message):  
        if not this.__logDebugs: return  
        log.debug(this.__wrapMessage(message))
        pass

    def __wrapMessage(this,message):
        this.__trySpamDailyLogs() 
        timestamp = _g.context.framework._getDatetime()
        
        #return str(timestamp) + message
        time = timestamp.strftime("%H:%M")
        
        #if timestamp.second!=0:
        #    time += ":{0}".format(timestamp.second)

        return str(time) + ": " + str(message)
        pass

    def debugAccumulateDaily(this,key,message):
        '''writes the log once a day to avoid spam.  includes timestamp automatically'''
        if not this.__logDebugs: return  
        msg = this.__wrapMessage(message)
        this.__storeToDailyLog(key,msg)

    def debugOnceDaily(this,key,message):
        if not this.__logDebugs: return  
        
        this.__storeToDailyLog(key,message)
        this.__recordHistory[key] = this.__recordHistory[key][0:1]
        this.__trySpamDailyLogs()
        pass
    def __storeToDailyLog(this,key,message):
        if not this.__recordHistory.has_key(key):
            this.__recordHistory[key] = []
        this.__recordHistory[key].append(message)

        pass

    def __trySpamDailyLogs(this):
        if _g.context.framework.thisFrameDay != this.__lastKnownDay:
            #new day, dump our previous logs
            this.__lastKnownDay = _g.context.framework.thisFrameDay   
            for key,values in this.__recordHistory.items():                         
                this.debug("YD_RECORD@{0}=\n{1}".format(key,",".join(values)))
                values[:] = [] #clear it
        pass

    def record(this, name,value, logDaily=False):                    
        this.__trySpamDailyLogs()            
        if(logDaily == True):
            this.__storeToDailyLog(name,"%0.4f" % value)
        record(**{name:value})

    def recordNormalized(this, name,value,baseline=1,subtract=0, logDaily=False):    
        '''normalize values to a 0 to 1 range'''

        if value - subtract == 0 or baseline == 0:
            toRecord = 0
        else:
            toRecord = (value - subtract) / baseline

        this.record(name,toRecord,logDaily=logDaily)

    #def getLastRecord(this,name):
    #    '''returns the last recorded value.  only exists if doing daily
    #    outputs, and during the day.  returns None if name not found'''
    #    return this.__recordHistory.get(name)
    pass

global logger
logger = Logger() #(logDebugs=False)

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
            #logger.info("{0} ordering {1}".format(security.qsec,amount))
            orderId = order(security.qsec,amount,limit_price,stop_price)
            return orderId
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

    #class _TradingAlgorithm_ZiplineShim(zipline.TradingAlgorithm):
    #    '''auto-generates a context to use'''
    #    def initialize(this):
    #        #delay initialize until start of first handle-data, so our
    #        #portfolio object is available
    #        #this.__isInitialized = False;
    #        this.context = Shims.Context()
    #        this.context.tradingAlgorithm = this            
    #        #this.context.portfolio = this.portfolio
    #        pass

    #    def handle_data(this,data):      
    #        this.context.portfolio = this.portfolio
    #        #if not this.__isInitialized:
    #        #    this.__isInitialized=True
    #        #    this.context.portfolio=this.portfolio
                
    #        this.context.framework._update(data)
    #        pass
    #    pass

class FrameHistory:
    def __init__(this,parent,framework, data):
        this.parent = parent
        this.framework = framework
        this.state = []
        this.isActive = this.parent.isActive
        #this.maxHistoryFrames = this.framework.maxHistoryFrames
        #assert(this.framework.simFrame == this.parent.simFrame, "parent frame
        #does not match")
        
        this.initialize(data)
    
    def initialize(this, data):
        '''overridable'''
        logger.error("FrameHistory.initialize() invoked.  You should override this method.")
        pass

    def constructFrameState(this,data):
        '''override and return the frame state, this will be prepended to history
        if you return NONE, the frame state (history) is not modified.'''   
        logger.error("FrameHistory.constructFrameState() invoked.  You should override this method.")             
        pass

    def _update(this,data):
        this.isActive = this.parent.isActive
        if not this.isActive:
            return

        

        currentState = this.constructFrameState(data)
        if(currentState != None):
            currentState.datetime = this.framework._getDatetime()
            currentState.simFrame = this.framework.simFrame

            this.state.insert(0,currentState)
            del this.state[this.framework.maxHistoryFrames:]

class StrategyPosition:
    '''allows two or more stratgies to controll their own positions (orders) for securities they care about, 
    without interfering with the orders of other strategies.

    To use:   each strategy should set security.myStrategyPositon.targetCapitalSharePercent, which is a percentage of your entire portfolio's value
    then execute the order (and/or rebalance) by invoking security.myStrategyPosition.processOrder()
    '''

    def __init__(this, security, strategyName):            
        this._security = security
        this._strategyName = strategyName
        this._lastOrderId = 0
        this._lastStopOrderId = 0
        this._currentCapitalSharePercent = 0.0
        this._currentShares = 0
        #for the last trade roundtrip, the aproximate returns.  set every time our percent changes to zero
        this._lastRoundtripReturns = 0.0
        #this is editable
        this.targetCapitalSharePercent = 0.0
        #price when we decided to order, not actually the fulfillment price
        this.__lastOrderPrice = 0.0
        this.__currentPeakGains = 0.0
        this.__currentPeakGainsDecay = 0.0
        this._currentReturns = 0.0 #returns of current open position. 
        this._totalTrades = 0 #total trades we execute via this strategyPosition.  note that due to partial fills, this may be less than actual trades

    def processOrder(this, data, rebalanceThreshholdPercent=0.05, maxLosses=None, maxGainsAdditionalDrawdown=None, maxGainsDecay=0.01): #, OBSOLETE_stopLimitPercent=0.0, OBSOLETE_momentumStopLimit = True, OBSOLETE_decayMomentum = 0.001):
        ''' set rebalanceThreshholdPercent to zero (0.0) to cause the position to readjust even if the targetPercentage doesn't change.   this is useful for reinvesting divideds / etc
        but is set to 0.05 (5 percent) so we don't spam orders 
        
        maxLosses:  close if our open position suffers a loss of this percent or more
        maxGainsAdditionalDrawdown : close if our open position's gains suffer a decrease of this+maxLosses or more.
        maxGainsDecay : over time this will reduce the acceptable gains drawdown (specified by maxGainsAdditionalDrawdown) so that on long-running gains we don't incur such a large drawdown before closing.
        '''
        #if momentumStopLimit == True (the default) we will stopLimitPercent based on the peak gains, not based on the original purchase price (this is generally a good ideas as it will maximize your gains)
        #decayMomentum : = if == 0.01 and using momentumStopLimit==True, we will decay the position's survival chances by 1% per tick until it's finally closed.
        
        if this._currentCapitalSharePercent == 0.0 and this.targetCapitalSharePercent == 0.0:
            #no work to do
            return 0



        currentPrice = data[this._security.qsec].close_price
        
        if this._currentCapitalSharePercent == this.targetCapitalSharePercent and this._currentCapitalSharePercent != 0.0:
            #update current returns
            this._currentReturns = (currentPrice - this.__lastOrderPrice) / this.__lastOrderPrice * math.copysign(1.0,this._currentCapitalSharePercent)
        else:
            #target is different so reset our returns as we are about to change our order
            this._currentReturns = 0.0


        if this._currentCapitalSharePercent == this.targetCapitalSharePercent and maxGainsAdditionalDrawdown != None:
            ##handle maxGains stoplimits
            gainsPercent = this._currentReturns - this.__currentPeakGainsDecay
            #if gainsPercent < -maxLosses:
            #    #loosing, so close out
            #    logger.debug("loosing, so close out.  gainsPercent={0}, maxLosses={1}".format(gainsPercent, maxLosses))
            #    this.targetCapitalSharePercent = 0.0 
            #else:

            if this._currentReturns > this.__currentPeakGains:
                this.__currentPeakGains = this._currentReturns
                this.__currentPeakGainsDecay = 0.0 #reset decay 
            else:
                #need to see if our gain exceed our stoplimitGains threshhold
                gainsFloorThreshhold = this.__currentPeakGains * maxGainsAdditionalDrawdown
                if gainsPercent < gainsFloorThreshhold:
                    lossesFromPeak = this.__currentPeakGains - gainsPercent
                    if maxLosses != None and lossesFromPeak < maxLosses:
                        #we are not yet exceeding maxLosses (from our peak) so don't close out yet
                        logger.debug("we are not yet exceeding maxLosses (from our peak) so don't close out yet.  \t {0} @ {1}, gains={2}".format(this._security.symbol,currentPrice,this._currentReturns))
                        pass
                    else:
                        #loosing from our peak, so close out
                        logger.debug("loosing from our peak, so close out.  gainsPercent={0:.4f}, \t gainsFloorThreshhold={1:.4f}, \t  lossesFromPeak={2:.4f}, \t  maxLosses={3:.4f}  \t this._currentReturns={4:.4f}".format(gainsPercent, gainsFloorThreshhold, lossesFromPeak, maxLosses,this._currentReturns))
                        this.targetCapitalSharePercent = 0.0 

                this.__currentPeakGainsDecay += (this.__currentPeakGains * maxGainsDecay)
        else:
            this.__currentPeakGains = 0.0
            this.__currentPeakGainsDecay = 0.0

        if this._currentCapitalSharePercent == this.targetCapitalSharePercent and this._currentCapitalSharePercent != 0.0:
            #handle maxlosses stoplimit
            if maxLosses != None and this._currentReturns < -maxLosses:
                logger.debug("maxlosses stoplimit.  this._currentReturns={0}, maxLosses={1}".format(this._currentReturns, maxLosses))
                this.targetCapitalSharePercent = 0.0


           

        if this.targetCapitalSharePercent == 0.0 and this._currentCapitalSharePercent != 0.0:
            #record our expected PnL
            this._lastRoundtripReturns = this._currentReturns

        this._currentCapitalSharePercent = this.targetCapitalSharePercent
        
        
           
        #determine value of percent
        targetSharesValue = this._security.framework.context.portfolio.portfolio_value * this._currentCapitalSharePercent
        targetSharesTotal = int(math.copysign(math.floor(abs(targetSharesValue / currentPrice)),targetSharesValue))
        
        targetSharesDelta = targetSharesTotal - this._currentShares

        if targetSharesTotal != 0:
            if abs(targetSharesDelta / (targetSharesTotal * 1.0)) < rebalanceThreshholdPercent:
                #logger.debug("{0} ORDER SKIPPED! {1} (change to small) : {2} + {3} => {4} shares".format(this.strategyName,this.security.symbol, this.currentShares, targetSharesDelta, targetSharesTotal))          
                #our position change was too small so we skip rebalancing
                return

        #do actual order
        if(abs(targetSharesDelta) >= 1): #can not perform an order on less than 1 share
            ####cancel previous open order, if any  #doesn't really work, as even when canceling, some shares may be filled so you'll be left in an uncomplete state
            ###lastOrder = get_order(this.lastOrderId)
            ###unfilled = lastOrder.amount - l
            ###cancel_order(this.lastOrderId)
            logger.info("{0} order {1} : {2} + {3} => {4} shares  \t \t decisionPrice={5} ".format(this._strategyName,this._security.symbol, this._currentShares, targetSharesDelta, targetSharesTotal,currentPrice))          
            this._lastOrderId = this._security.framework.tradingAlgorithm.order(this._security.sid,targetSharesDelta,None,None)
            this._currentShares = targetSharesTotal
            this.__lastOrderPrice = currentPrice
            this._totalTrades += 1
            this._security.framework._totalTrades += 1
            
            return this._lastOrderId
        else:
            return 0

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
            this.security_end_date = datetime.datetime(1990,1,1) #Datetime: The date when this security stopped trading (= yesterday for securities that are trading normally, because that's the last day for which we have historical price data).
    
    

    def __init__(this,sid, framework):
        this.sid = sid  
        this.isActive = False
        this.framework = framework
        this.security_start_date = datetime.datetime.utcfromtimestamp(0)
        this.security_end_date = datetime.datetime.utcfromtimestamp(0)
        this.simFrame = -1
        this.security_start_price = 0.0
        this.security_end_price = 0.0
        #this.daily_open_price = [0.0]
        #this.daily_close_price = [0.0]
        this.symbol = "??? Not yet active so symbol not known"
        
        
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

        
        
        #update qsec to most recent (if any) 67
        this.qsec = qsec
        if qsec:
            this.isActive = True
            this.symbol = qsec.symbol
            #assert(qsec.sid == this.sid,"security.update() sids do not match")
            
            if this.security_start_price == 0.0:
                this.security_start_price = data[this.sid].close_price
            this.security_end_price = data[this.sid].close_price

            this.security_start_date = qsec.security_start_date
            this.security_end_date = qsec.security_end_date
        else:
            this.isActive = False

        #try:
        #    this.daily_close_price =
        #    this.framework.daily_close_price[this.qsec]
        #    this.daily_open_price = this.framework.daily_open_price[this.qsec]
        #except:
        #    this.daily_close_price = []
        #    this.daily_open_price = []

        #if len(this.daily_close_price) == 0 or len(this.daily_open_price) ==
        #0:
        #    this.isActive = False
class FrameworkBase():
    def __init__(this, context, data, maxHistoryFrames=60): #5 days of history
        this.maxHistoryFrames = maxHistoryFrames
        this.__isFirstTimestepRun = False
        this.context = context
        this.tradingAlgorithm = Shims._TradingAlgorithm_QuantopianShim() #prepopulate to allow intelisence
        this.tradingAlgorithm = context.tradingAlgorithm
        this.simFrame = -1 #the current timestep of the simulation
        this.framesToday = -1 #number of frames executed today
        
        this.allSecurities = {} #dictionary of all securities, including those not targeted
        this.activeSecurities = {}

        this.thisFrameDay = 0
        this.lastFrameDay = 0

        this._totalTrades = 0 #total trades we execute via all strategyPositions.  note that due to partial fills, this may be less than actual trades

        this.isIntradayRunDetected = False #if we are running in intraday, this will be set to true on frame 2.  the 2nd bar will be in the same day as the first bar.  no better way to detect unfortunately.

        #for storing quantopian history
        #this.daily_close_price = pandas.DataFrame()
        #this.daily_open_price = pandas.DataFrame()
        
        this._initialize(data)

        pass
    def ensureMinHistory(this, minFrames):
        '''increases the history frames if the current is less than your required min.  
        this is a good way to set your history, as too much history will slow down your sim, and can crash it due to out-of-memory'''

        if this.maxHistoryFrames < minFrames:
            this.maxHistoryFrames = minFrames      
    
    def _initialize(this, data):
        '''starts initialiation of the framework
        do not override this, or any other method starting with an underscore.
        methods without an underscore prefix can and should be overridden.'''
        #do init here
        this.initialize(data)        
        pass

    def initialize(this, data):
        '''override this to do your init'''
        logger.error("You should override FrameworkBase.initialize()")
        pass


    def initializeFirstUpdate(this,data):
        '''override this.  called the first timestep, before update.  
        provides access to the 'data' object which normal .initialize() does not'''
        logger.error("You should override FrameworkBase.initializeFirstUpdate()")
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
            #this.daily_close_price = history(bar_count=180, frequency='1d',
            #field='close_price')
            #this.daily_open_price = history(bar_count=180, frequency='1d',
            #field='open_price')
            this.framesToday = 0
        else:
            this.framesToday += 1
            this.isIntradayRunDetected = True

        this.__updateSecurities(data)
        

        if not this.__isFirstTimestepRun:
            this.__isFirstTimestepRun = True
            this.initializeFirstUpdate(data)

        this.update(data)
        pass

    def update(this,data):
        '''override and update your usercode here'''
        logger.error("You should override FrameworkBase.update()")
        pass

    def __updateSecurities(this,data):
        '''get all qsecs from data, then update the targetedSecurities accordingly'''
        #logger.debug("FrameworkBase.__updateSecurities() start.
        #allSecLength={0}".format(len(this.allSecurities)))
        #convert our data into a dictionary
        currentQSecs = {}
        newQSecs = {}
        for qsec in data:            
            #if online, qsec is a securities object
            sid = qsec.sid      
            
            #logger.debug("FrameworkBase.__updateSecurities() first loop, found
            #{0}, sid={1}.  exists={2}".format(qsec,
            #sid,this.allSecurities.has_key(sid) ))

            currentQSecs[sid] = qsec
            #determine new securities found in data
            if not this.allSecurities.has_key(sid):
                logger.debug("FrameworkBase.__updateSecurities() new security detected.  will construct our security object for it: {0}".format(qsec))
                newQSecs[sid] = qsec


        #construct new Security objects for our newQSecs
        for sid, qsec in newQSecs.items():            
            #assert(not
            #this.allSecurities.has_key(sid),"frameworkBase.updateSecurities
            #key does not exist")
            #logger.debug("FrameworkBase.__updateSecurities() new security
            #found {0}".format(qsec))
            this.allSecurities[sid] = this._getOrCreateSecurity(qsec, data)

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
                #logger.debug("FrameworkBase.__updateSecurities() NOT ACTIVE
                #{0}".format(security.qsec))
                continue
            #logger.debug("FrameworkBase.__updateSecurities() ACTIVE
            #{0}".format(security.qsec))
            this.activeSecurities[sid] = security
            pass

        pass

    def initializeSecurity(this,security, data):
        '''override to do custom init logic on each security. 
        if you wish to use your own security, return it (it will replace the existing)'''
        logger.error("You should override FrameworkBase.initializeSecurity()")
        pass       
             
    def _getOrCreateSecurities(this,qsecArray, data):
        '''pass in an array of quantopian sid/sec tuples  (ex:  [(24,sid(24)),(3113,sid(3113))]) 
        and returns an array of unique security objects wrapping them.   duplicate sids are ignored'''

        securities = {}

        for qsec in qsecArray:            
            security = this._getOrCreateSecurity(qsec, data)
            securities[security.sid] = security
            pass

        return securities.values()

    def _getOrCreateSecurity(this, qsec, data):
        '''pass in a quantopian sec (ex:  sid(24)) and returns our security object wrapping it
        if the security object
        '''
        
        sid = qsec.sid
        if this.allSecurities.has_key(sid):
            return this.allSecurities[sid]

        #does not exist, have to create
        newSecurity = Security(sid,this)
        #new, so do our framework's custom init logic on this security
        maybeNewSec = this.initializeSecurity(newSecurity, data)
        if maybeNewSec is not None:
            #framework replaced newSec with a different sec
            newSecurity = maybeNewSec
                
        this.allSecurities[sid] = newSecurity
        
        return newSecurity
        pass


    def _getDatetime(this):
        '''returns current market time, using US/Eastern timezone'''
        #if is_offline_Zipline:
        #    if len(this.allSecurities) == 0:
        #        #return datetime.datetime.fromtimestamp(0,pytz.UTC)
        #        return
        #        pandas.Timestamp(datetime.datetime.fromtimestamp(0,pytz.UTC)).tz_convert('US/Eastern')
        #    else:
        #        assert(False,"need to fix this to return something valid.  all
        #        securities isn't good enough.  probably search for first
        #        active")
        #        return this.allSecurities.values()[0].datetime
        #else:
        #    return get_datetime()
        #pass
        return pandas.Timestamp(pandas.Timestamp(get_datetime()).tz_convert('US/Eastern'))
#entrypoints

def handle_data(context=Shims.Context(),data=pandas.DataFrame()):   
    '''update method run every timestep on quantopian'''
    
    #try: 
    if context.firstFrame:
        #'''init on our first frame'''
        context.firstFrame = False
        context.tradingAlgorithm = Shims._TradingAlgorithm_QuantopianShim()
        context.tradingAlgorithm.context = context
        context.framework = constructFramework(context,data)
        
    
    context.framework._update(data)
    #except Exception,e:
    #    print "Caught:",e

    pass

class Global():
    pass
global _g
_g = Global()



def initialize(context=Shims.Context()):
    '''initialize method used when running on quantopian'''
    context.firstFrame = True 
    
    _g.context = context
    #context.spy = sid(8554) #SPY
    ########## SET UNIVERSE
    #if you need set universe, do it here (note that doing this slows the algo
    #considerably)
    #set_universe(universe.DollarVolumeUniverse(floor_percentile=90.0,ceiling_percentile=100.0))
    #context.universe = [#sid(698)         #BA
    #    #sid(8554) #SPY
    #    #sid(27098) #ISE

    #    ####################### 9 sector etfs
    #    sid(19662) # XLY Consumer Discrectionary SPDR Fund
    #    ,sid(19656) # XLF Financial SPDR Fund
    #    ,sid(19658) # XLK Technology SPDR Fund
    #    ,sid(19655) # XLE Energy SPDR Fund
    #    ,sid(19661) # XLV Health Care SPRD Fund
    #    ,sid(19657) # XLI Industrial SPDR Fund
    #    ,sid(19659) # XLP Consumer Staples SPDR Fund
    #    ,sid(19654) # XLB Materials SPDR Fund
    #    ,sid(19660) # XLU Utilities SPRD Fund
    #    ]

    #aprox 200 SPY constituents from fetcher
    #fetch_csv(
    #   "https://googledrive.com/host/0BwZ2bMDOKaeDYWYzYzgxNDYtNmQyYi00ZDk5LWE3ZTYtODQ0ZDAzNTBkY2M4/trading/SP500-20131001.csv",
    #    pre_func=preview,
    #    date_column='date',
    #    universe_func=(my_universe))
    #aprox 90 hardcoded SPY constituents
    #my_static_universe(context) 

    ########## COMMISSION
    #use top to decrease uncertainty when testing algorithms
    #set_commission(commission.PerShare(cost=0.0))
    #set_commission(commission.PerShare(cost=0.005, min_trade_cost=1.00)) #IB
    #fixed commission model
    #set_commission(commission.PerShare(cost=0.013, min_trade_cost=1.3)) #more
    #agressive...
    
    ########## SLIPPAGE
    #use top to decrease uncertainty when testing algorithms
    #set_slippage(slippage.FixedSlippage(spread=0.00))
    #set_slippage(slippage.FixedSlippage(spread=0.01))
    #set_slippage(WorstSpreadSlippage())
    #set_slippage(CustomSlippage(1.0,0.0))

    ############# Anony values
    set_commission(commission.PerTrade(cost=1.0))
    set_slippage(TradeAtTheOpenSlippageModel_Simple(0.1))

##############  USERCODE BELOW.  EDIT BELOW THIS LINE
##############  USERCODE BELOW.  EDIT BELOW THIS LINE
##############  USERCODE BELOW.  EDIT BELOW THIS LINE


class BBTechnicalIndicators(FrameHistory):
    '''technical indicators relating to bollinger bands'''
    class State:
        '''State recorded for each frame (minute).  number of frames history we store is determined by framework.maxHistoryFrames'''
        def __init__(this,parent, security, data):
            this.parent = parent
            this.security = security
            this.history = this.parent.state

            bb = this.parent.bbands_data[this.security.sid]
            #will be NaN if not enough period
            this.upperLimit = bb[0]
            this.line = bb[1]
            this.lowerLimit = bb[2]
            #see https://www.tradingview.com/stock-charts-support/index.php/Bollinger_Bands_%25B_(%25B)
            this.percentB = (this.security.standardIndicators.state[0].close_price - this.lowerLimit) / (this.upperLimit - this.lowerLimit)
            #see https://www.tradingview.com/stock-charts-support/index.php/Bollinger_Bands_Width_(BBW)
            this.bbw = (this.upperLimit - this.lowerLimit) / this.line
            #track slope of %B, to determine if rising (positive) or falling (negative)
            if len(this.history) > 0:
                this.percentBSlope = (this.percentB - this.history[0].percentB)
                this.bbwSlope = (this.bbw - this.history[0].bbw)
                this.percentBPercentile = scipy.stats.percentileofscore([state.percentB for state in this.history],this.percentB,"mean") / 100.0
                this.bbwPercentile = scipy.stats.percentileofscore([state.bbw for state in this.history],this.bbw,"mean") / 100.0 
                this.lineSlope = (this.line - this.history[0].line)
            else:
                this.percentBSlope = 0.0
                this.bbwSlope = 0.0
                this.percentBPercentile = 0.5
                this.bbwPercentile = 0.5
                this.lineSlope = 0.0

            #track momentum
            if this.percentB > 0.8:
                if len(this.history) > 0:
                    this.upperMomentumTicks = this.history[0].upperMomentumTicks + 1
                else:
                    this.upperMomentumTicks = 1
            else:
                this.upperMomentumTicks = 0            
            if this.percentB < 0.2:
                if len(this.history) > 0:
                    this.lowerMomentumTicks = this.history[0].lowerMomentumTicks + 1
                else:
                    this.lowerMomentumTicks = 1
            else:
                this.lowerMomentumTicks = 0





            #logger.debug(" bb for {0} is {1}".format(this.security.symbol, bb));
            
            #logger.recordNormalized("upperLimit",this.upperLimit,this.security.security_start_price)
            #logger.recordNormalized("line",this.line,this.security.security_start_price)
            #logger.recordNormalized("lowerLimit",this.lowerLimit,this.security.security_start_price)

            #logger.record("upperBar",1.0)
            #logger.record("lowerBar",0.0)
            #logger.record("upperApproach",0.8)
            #logger.record("lowerApproach",0.2)
            #logger.record("percentB",this.percentB);

        def __repr__(this):
            return "{0} @ {1} BBANDS l={2:.2f} \t upper={3:.2f} lower={4:.2f}".format(this.security.symbol, this.datetime, this.line, this.upperLimit, this.lowerLimit)


    def initialize(this, data):
        this.bbands = ta.BBANDS(timeperiod=20,nbdevup=2, nbdevdn=2,matype=0) #output: Dictionary of sid to tuples, where each tuple is three floats: (upperLimit, line, lowerLimit).
        this.bbands_data = this.bbands(data)
        pass
    
    def constructFrameState(this,data):
        #logger.debug("BBTechnicalIndicators.constructFrameState")
        currentState = BBTechnicalIndicators.State(this, this.parent, data)
        return currentState

class StandardIndicators(FrameHistory):
    '''common technical indicators that we plan to use for any/all strategies
    feel free to extend this, or use as a reference for constructing specialized technical indicators'''
    class State:
        '''State recorded for each frame (minute).  number of frames history we store is determined by framework.maxHistoryFrames'''
        def __init__(this,parent, security, data):
            this.parent = parent
            this.security = security
            this.history = this.parent.state

            #preset for proper intelisence
            this.datetime = datetime.datetime.now()
            this.open_price = 0.0
            this.close_price = 0.0
            this.high = 0.0
            this.low = 0.0
            this.volume = 0

            #this.mavg3 = 0.0
            #this.mavg7 = 0.0
            #this.mavg15 = 0.0
            #this.mavg30 = 0.0
            #this.mavg45 = 0.0
            #this.mavg60 = 0.0

            #this.stddev3 = 0.0
            #this.stddev7 = 0.0
            #this.stddev15 = 0.0
            #this.stddev30 = 0.0
            #this.stddev45 = 0.0
            #this.stddev60 = 0.0

            this.datetime = data[this.security.qsec].datetime
            this.open_price = data[this.security.qsec].open_price
            this.close_price = data[this.security.qsec].close_price
            this.high = data[this.security.qsec].high
            this.low = data[this.security.qsec].low
            this.volume = data[this.security.qsec].volume
                        
            
            #mavg for last x minutes
            #this.mavg3 = numpy.mean([state.close_price for state in
            #this.history[0:3]])
            #this.mavg7 = numpy.mean([state.close_price for state in
            #this.history[0:7]])
            #this.mavg15 = numpy.mean([state.close_price for state in
            #this.history[0:15]])
            #this.mavg30 = numpy.mean([state.close_price for state in
            #this.history[0:30]])
            #this.mavg45 = numpy.mean([state.close_price for state in
            #this.history[0:45]])
            #this.mavg60 = numpy.mean([state.close_price for state in
            #this.history[0:60]])

            #this.stddev3 = numpy.std([state.close_price for state in
            #this.history[0:3]])
            #this.stddev7 = numpy.std([state.close_price for state in
            #this.history[0:7]])
            #this.stddev15 = numpy.std([state.close_price for state in
            #this.history[0:15]])
            #this.stddev30 = numpy.std([state.close_price for state in
            #this.history[0:30]])
            #this.stddev45 = numpy.std([state.close_price for state in
            #this.history[0:45]])
            #this.stddev60 = numpy.std([state.close_price for state in
            #this.history[0:60]])

            if len(this.history) < 1:                
                this.returns = 0.0
                this.returns_median_abs = 0.0
            else:
                #always returns compared to last timestep
                this.returns = (this.close_price - this.history[0].close_price) / this.history[0].close_price
                if len(this.history) == 1:
                    this.returns_median_abs = abs(this.returns)
                else:
                    this.returns_median_abs = numpy.median([abs(state.returns) for state in this.history])

            try:                
                #when in intraday mode, stores cumulative returns through the day
                this.returns_today = data[this.security.qsec].returns()
            except:
                this.framework.logger.error("{0} unable to obtain returns()  setting returns to zero  open={1}.  close = {2}".format(this.parent.qsec, this.open_price, this.close_price))
                this.returns_today = 0.0
            pass

            #daily accumulations
            if this.security.framework.thisFrameDay != this.security.framework.lastFrameDay or len(this.history) < 1:
                this.open_price_today = this.open_price
                #if len(this.history) < 1:
                    
                #    this.open_price_yesterday = this.open_price_today
                #    this.close_price_yesterday = this.close_price
                #    this.returns_yesterday = this.returns_today
                ##new day, so record our start of day values
                #else:
                #    this.open_price_yesterday =
                #    this.history[0].open_price_today
                #    this.close_price_yesterday = this.history[0].close_price
                #    this.returns_yesterday = this.history[0].returns_today
            else:
                this.open_price_today = this.history[0].open_price_today
                #this.open_price_yesterday =
                #this.history[0].open_price_yesterday
                #this.close_price_yesterday =
                #this.history[0].close_price_yesterday
                #this.returns_yesterday = this.history[0].returns_yesterday

        def __repr__(this):
            return "{0} @ {1} c={0}".format(this.security.symbol, this.datetime, this.close_price)

    def initialize(this, data):
        pass
    
    def constructFrameState(this,data):
        #logger.debug("StandardTechnicalIndicators.constructFrameState")
        currentState = StandardIndicators.State(this, this.parent, data)
        return currentState


class DailyTechnicalIndicators(FrameHistory):
    '''standard technical indicators for the entire day
    for daily history.   the .state[] history does not include the current day, only previous days'''
    class State:
        '''State recorded for each previous day.  number of frames history we store is determined by framework.maxHistoryFrames'''
        def __init__(this,parent, security, data):
            this.parent = parent
            this.security = security
            this.history = this.parent.state



            #preset for proper intelisence
            this.datetime = datetime.datetime.now()


            #setting these to default to yesterday's value so that for the
            #first day of our simulation we get reasonable values
            this.open_price = data[this.security.qsec].mavg(1)
            this.close_price = this.open_price
            #this.high = 0.0
            #this.low = 0.0
            #this.volume = 0

            #this.mavg3 = this.open_price
            #this.mavg7 = this.open_price
            #this.mavg15 = this.open_price
            #this.mavg30 = this.open_price
            #this.mavg45 = this.open_price
            #this.mavg60 = this.open_price

            #this.stddev3 = this.open_price
            #this.stddev7 = this.open_price
            #this.stddev15 = this.open_price
            #this.stddev30 = this.open_price
            #this.stddev45 = this.open_price
            #this.stddev60 = this.open_price

            
            if this.security.simFrame != 0:
                #assert(this.security.standardIndicators.state[1].simFrame+1 ==
                #this.security.simFrame,"expect to be previous day")
            
                this.datetime = this.security.standardIndicators.state[1].datetime
                this.open_price = this.security.standardIndicators.state[1].open_price_today
                this.close_price = this.security.standardIndicators.state[1].close_price
                this.returns = this.security.standardIndicators.state[1].returns_today

            
            #mavg for last x days
            #this.mavg3 = data[this.security.qsec].mavg(3)
            #this.mavg7 = data[this.security.qsec].mavg(7)
            #this.mavg15 = data[this.security.qsec].mavg(15)
            #this.mavg30 = data[this.security.qsec].mavg(30)
            #this.mavg45 = data[this.security.qsec].mavg(45)
            #this.mavg60 = data[this.security.qsec].mavg(60)

            #this.stddev3 = data[this.security.qsec].stddev(3)
            #this.stddev7 = data[this.security.qsec].stddev(7)
            #this.stddev15 = data[this.security.qsec].stddev(15)
            #this.stddev30 = data[this.security.qsec].stddev(30)
            #this.stddev45 = data[this.security.qsec].stddev(45)
            #this.stddev60 = data[this.security.qsec].stddev(60)

        def __repr__(this):
            return "c={0} mavg7={1} mavg30={2}".format(this.close_price,this.mavg7,this.mavg30)

    def initialize(this, data):
        pass
    
    def constructFrameState(this,data):
        #logger.debug("StandardTechnicalIndicators.constructFrameState")

        if this.framework.thisFrameDay == this.framework.lastFrameDay:
            #keep previous
            currentState = None
        else:
            currentState = DailyTechnicalIndicators.State(this, this.parent, data)

        return currentState
    pass



class VolatilityBiasIndicators(FrameHistory):
    ''' custom indicators used by the volatility bias strategy '''
    def initialize(this, data):
        
        pass
    
    def setWindow(this, trendPeriods, weightPeriods, triggerPeriods):
        '''set the size of the window our volatilityBias cares about
        trendPeriods #state.trend = percent the range is up, exponential weighted by timestep
        weightPeriods #state.weight = percent the range is up, linear weighted by timestep
        triggerPeriods #state.trigger = percent the range is up, linear weighted by timestep
        '''

        #internal variables
        this.trendPeriods = trendPeriods #the max history we will care about, used for determining the value of the state.trend variable
        this.weightPeriods = weightPeriods
        this.triggerPeriods = triggerPeriods
        
        this.framework.ensureMinHistory(this.trendPeriods)
        this.framework.ensureMinHistory(this.weightPeriods)
        this.framework.ensureMinHistory(this.triggerPeriods)

    '''technical indicators relating to bollinger bands'''
    class State:
        '''State recorded for each frame (minute).  number of frames history we store is determined by framework.maxHistoryFrames'''
        def __init__(this,parent, security, data):
            this.parent = parent
            this.security = security
            this.history = this.parent.state

            this.setWeight()

        def setWeight(this):
            '''computes weight by taking the price range (high-low) for each timestep, and summing them based on linear weight (most recient = more weight)'''
            #pretty confident in this port being accurate
            security = this.security
            stdState = security.standardIndicators.state

            if len(this.history)<this.parent.trendPeriods:
                this.weight = 0.0
                this.trend = 0.0
                this.trigger = 0.0
            else:
                #SET state.trend
                #trading range linear weighted by timestep
                upPortion = 0.0
                downPortion = 0.0
                span = this.parent.trendPeriods
                for i in range(0,span):
                    if stdState[i].close_price > stdState[i].open_price:
                        upPortion += ((span-i) * stdState[i].high - stdState[i].low);  
                    else:
                        downPortion +=((span-i) * stdState[i].high - stdState[i].low);  
                if (upPortion + downPortion > 0.0):
                    factor = upPortion / (upPortion + downPortion)
                    #trend = percent the range is up, exponential weighted by timestep
                    this.trend = (this.history[0].trend + factor) / 2.0
                
                #SET state.weight
                upPortion = 0.0
                downPortion = 0.0
                span = this.parent.weightPeriods
                for i in range(0,span):
                    if stdState[i].close_price > stdState[i].open_price:
                        upPortion += ((span-i) * stdState[i].high - stdState[i].low);  
                    else:
                        downPortion +=((span-i) * stdState[i].high - stdState[i].low);  
                if (upPortion + downPortion > 0.0):
                    factor = upPortion / (upPortion + downPortion)
                    #weight = percent the range is up, linear weighted by timestep
                    this.weight = factor

                #SET state.trigger
                upPortion = 0.0
                downPortion = 0.0
                span = this.parent.triggerPeriods
                for i in range(0,span):
                    if stdState[i].close_price > stdState[i].open_price:
                        upPortion += ((span-i) * stdState[i].high - stdState[i].low);  
                    else:
                        downPortion +=((span-i) * stdState[i].high - stdState[i].low);  
                if (upPortion + downPortion > 0.0):
                    factor = upPortion / (upPortion + downPortion)
                    #trigger = percent the range is up, linear weighted by timestep
                    this.trigger = factor

            return this.weight
        def __repr__(this):
            return "{0} @ {1} VOLBIAS weight={2:.2f} \t trend={3:.2f} trigger={4:.2f}".format(this.security.symbol, this.datetime, this.weight, this.trend, this.trigger)
            


    
    def constructFrameState(this,data):
        #logger.debug("VolatilityBiasIndicators.constructFrameState")
        currentState = VolatilityBiasIndicators.State(this, this.parent, data)
        return currentState    

class VolatilityBiasStrategy():
    def __init__(this, framework, data):
        this.framework = framework


        pass

    def initialize(this,data):
        
        this.trendPeriods = 53
        this.weightPeriods = 33
        this.triggerPeriods = 4

        #this.universe = this.framework._getOrCreateSecurities([
        #    sid(12915) # MDY SPDR S&P MIDCAP 400 ETF TRUST
        #    ,sid(19654) # XLB Materials Select Sector SPDR 
        #    ,sid(19655) # XLE Energy Select Sector SPDR
        #    ,sid(19656) # XLF Financial Select Sector SPDR 
        #    ,sid(19657)# XLI Industrial Select Sector SPDR
        #    ,sid(19658)#XLK  Industrial Select Sector SPDR
        #    ,sid(19659) # XLP  Consumer Staples Select Sector SPDR
        #    ,sid(19660)# XLU Utilities Select Sector SPDR
        #    ,sid(19661)# XLV Utilities Select Sector SPDR
        #    ,sid(19662) # XLY Consumer Discretionary Select Sector SPDR
        #    ,sid(25485) # AGG ISHARES CORE U.S. AGGREGATE BONDS
        #    ],data)

        this.universe = this.framework._getOrCreateSecurities([
            sid(19920) # QQQ
            , sid(2174) # DIA
            , sid(24705) # ISHARES MSCI EMERGING MARKETS "EEM"
            , sid(22972) # ISHARES MSCI EAFE ETF "EFA"
            , sid(24744) # GUGGENHEIM S&P 500 EQUAL WEIGH "RSP",
            , sid(19654) # Materials Select Sector SPDR              "XLB"
            , sid(19655) # Energy Select Sector SPDR                 "XLE"
            , sid(19656) # Financial Select Sector SPDR              "XLF"
            , sid(19657) # Industrial Select Sector SPDR             "XLI"
            , sid(19658) # Technology Select Sector SPDR            "XLK"
            , sid(19659) # Consumer Staples Select Sector SPDR        "XLP"
            , sid(19660) # Utilities Select Sector SPDR              "XLU"
            , sid(19661) # Healthcare Select Sector SPDR            "XLV"
            , sid(19662) # Consumer Discretionary Select Sector SPDR "XLY"
            , sid(22739) # VANGUARD TOTAL STOCK MARKET ETF "VTI"
            , sid(25901) # VANGUARD SMALL-CAP VALUE ETF "VBR"
            , sid(25485) # ISHARES CORE U.S. AGGREGATE BONDS "AGG"
     
            ,  sid(2)     #   Alcoa "AA"
            , sid(679)   #   Amex "AXP"
            ,  sid(698)   #   BOEING CO   "BA"
            , sid(700)   #   BANK OF AMERICA CORP   "BAC"
            , sid(734)   #   BAXTER INTERNATIONAL INC   "BAX"
            , sid(1267)  #   CATERPILLAR INC   "CAT"
            ,sid(1900)  #   CISCO SYSTEMS INC   "CSCO"
            , sid(23112) #   CHEVRON CORPORATION   "CVX"
            ,  sid(2119)  #   DU PONT DE NEMOURS E I &CO   "DD"
            , sid(2190)  #   WALT DISNEY CO-DISNEY COMMON   "DIS"
            , sid(8347)  #   EXXON MOBIL CORPORATION          "XOM"
            ,  sid(3149)  #   GENERAL ELECTRIC CO     "GE"
            ,  sid(3496)  #   HOME DEPOT INC  "HD"
            , sid(3735)  #   HEWLETT-PACKARD CO   "HPQ"
            , sid(3766)  #   INTL BUSINESS MACHINES CORP   "IBM"
            ,sid(3951)  #   INTEL CORP   "INTC"
            , sid(4151)  #   JOHNSON AND JOHNSON   "JNJ"
            , sid(25006) #   JPMORGAN CHASE & CO COM STK   "JPM"
            ,  sid(4283)  #   COCA-COLA CO   "KO"
            , sid(4707)  #   MCDONALDS CORP   "MCD"
            , sid(4922)  #   3M COMPANY   "MMM"
            , sid(5029)  #   MERCK & CO IN C  "MRK"
            ,sid(5061)  #   MICROSOFT CORP   "MSFT"
            , sid(5923)  #   PFIZER INC   "PFE"
            ,  sid(5938)  #   PROCTER & GAMBLE CO   "PG"
            ,   sid(6653)  #   AT&T INC.COM   "T"
            , sid(24845) #   Travelers "TRV"
            , sid(7792)  #   UNITEDHEALTH GROUP INC  "UNH"
            , sid(7883)  #   UNITED TECHNOLOGIES CORP   "UTX"
            ,  sid(21839) #   VERIZON COMMUNICATIONS   "VZ"
            , sid(8229)  #   WAL-MART STORES INC  "WMT"
    ],data)

    def update(this, data):
        
        if this.framework.simFrame < this.weightPeriods:
            #ensure we have our history populated
            return

        totalWeight = 0
        entries = [] #securities we will open positions with
        exits = [] #open positions we will close

        securitiesToEnumerate = this.framework.activeSecurities.items()

        for sid,security in securitiesToEnumerate:
            enter = False
            exit = False
            if security.isActive==False:
                continue

            volBiasState = security.volIndicators.state[0]
            
            if volBiasState.weight - volBiasState.trigger >= 0.40 and volBiasState.trend > 0.50:
                enter = True
            elif security.volatilityBiasStrategyPosition._currentCapitalSharePercent > 0.0:
                if volBiasState.trigger > 0.50 and volBiasState.trigger < 0.80:
                    enter = True
                else: 
                    exit = True
            else:
                exit = True

            if enter:                
                totalWeight += volBiasState.weight
                entries.append(security)
            if exit:
                exits.append(security)
                pass
            pass
        enterCount = len(entries)
        if enterCount > 0:
            for security in entries:
                #rebalance based on weights
                security.volIndicators.state[0].weight /= totalWeight
                security.volatilityBiasStrategyPosition.targetCapitalSharePercent = security.volIndicators.state[0].weight
        for security in exits:
            security.volatilityBiasStrategyPosition.targetCapitalSharePercent = 0.0
            pass

        for sid,security in securitiesToEnumerate:
            #execute trades for this timestep
            security.volatilityBiasStrategyPosition.processOrder(data)
            
       



    
    
class ExampleFramework(FrameworkBase):
    def initialize(this, data):
        
        this.volatilityBiasStrategy = VolatilityBiasStrategy(this,data)
        this.volatilityBiasStrategy.initialize(data)
        
        #this.spy = this._getOrCreateSecurity(sid(8554), data) #SPY
        

        pass

    def initializeFirstUpdate(this, data):
        #this.ensureMinHistory(360)
        pass

    def initializeSecurity(this,security, data):
        security.standardIndicators = StandardIndicators(security,this, data)
        #security.dailyIndicators = DailyTechnicalIndicators(security,this)
        security.volIndicators = VolatilityBiasIndicators(security,this, data)
        #set our securities to use the same window sizes based on a global config
        security.volIndicators.setWindow(this.volatilityBiasStrategy.trendPeriods, this.volatilityBiasStrategy.weightPeriods, this.volatilityBiasStrategy.triggerPeriods)
        security.volatilityBiasStrategyPosition = StrategyPosition(security,"volatilityBiasStrategyPosition")
        
        
        pass

    def update(this, data):

        if this.isIntradayRunDetected:
            this.minimumDifficulty = 0.99
        else:
            this.minimumDifficulty = 0.8

        #update all security indicators
        for sid,security in this.activeSecurities.items():
            security.standardIndicators._update(data)
            #security.dailyIndicators._update(data)
            security.volIndicators._update(data)
            pass

        this.volatilityBiasStrategy.update(data)

        logger.record("tradesD100",this._totalTrades / 100.0)

        #record(port_value = this.context.portfolio.portfolio_value, pos_value
        #= this.context.portfolio.positions_value , cash =
        #this.context.portfolio.cash)

    pass





##############  CONFIGURATION BELOW
def constructFramework(context,data):
    '''factory method to return your custom framework/trading algo'''
    return ExampleFramework(context,data)
