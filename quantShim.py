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


#quantopian shims
class Shims():
    class Context():
        def __init__(this , portfolio = zipline.protocol.Portfolio()): #, tradingAlgorithm = zipline.TradingAlgorithm()):
            this.portfolio = portfolio
            #this.tradingAlgorithm = tradingAlgorithm        
            pass
        pass

    

    class _Logger():
        '''shim for exposing the same logging definitions to visualstudio intelisence'''
        def __init__(this, framework):
            this.framework = framework;
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
                security = this.context.framework.targetedSecurities[sid]
            log.info("{0} ordering {1}".format(security.qsec,amount))
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
            #delay initialize until start of first handle-data, so our portfolio object is available            
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


class FrameStateBase:
    '''used to store state about the current frame of the simulation, and access the history'''
    def __init__(this, parent, framework):
        this.parent=parent
        this.framework = framework

    def initializeAndPrepend(this,history, data, maxHistoryFrames = None):            
        '''inserts itself into the first slot of history and trims to max this.framework.maxHistoryFrames
        DO NOT OVERRIDE.  override .initialize() instead
        '''
        if maxHistoryFrames is None:
           maxHistoryFrames = this.framework.maxHistoryFrames
        
        this.history = history
        this.maxHistoryFrames = maxHistoryFrames
        this.history.insert(0,this)
        this.history[0:maxHistoryFrames]            
        ##init
        this.datetime = this.framework.get_datetime()
        this.simFrame = this.framework.simFrame

        this.initialize(data)
        

    def initialize(this, data):
        '''override this to hook ending of .initializeAndPrepend()'''
        pass

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
    '''allows multiple independent positions per security'''

    def __init__(this, security):            
        this.security = security
        this.lastOrderId = 0
        this.lastStopOrderId = 0
        this.currentCapitalSharePercent = 0.0
        this.currentShares = 0
        #this is editable
        this.targetCapitalSharePercent = 0.0

    def processOrder(this):
        this.currentCapitalSharePercent = this.targetCapitalSharePercent
        #determine value of percent
        targetSharesTotal = this.security.framework.context.portfolio.portfolio_value * this.currentCapitalSharePercent / this.security.state[0].close_price
        targetSharesDelta = targetSharesTotal - this.currentShares
        
        this.lastOrderId = this.security.framework.tradingAlgorithm.order(this.security.sid,targetSharesDelta)            
        this.currentShares = targetSharesTotal

class Security:
    isDebug = False

    class State(FrameStateBase):
        '''used to store state about the current frame of the simulation, and access the history'''
        
        def initialize(this,data):
            this.isActive = this.parent.isActive
            assert(this.framework.simFrame==this.parent.simFrame)
            if not this.isActive:
                return

            #preset for proper intelisence
            this.datetime = datetime.datetime.now()
            this.open_price = 0.0
            this.close_price = 0.0
            this.high = 0.0
            this.low = 0.0
            this.volume = 0

            this.datetime = data[this.parent.qsec].datetime
            this.open_price = data[this.parent.qsec].open_price
            this.close_price = data[this.parent.qsec].close_price
            this.high = data[this.parent.qsec].high
            this.low = data[this.parent.qsec].low
            this.volume = data[this.parent.qsec].volume

            
            this.__voters = 0
            
            this._voteLong = 0
            this._voteShort = 0
            this._voteHold = 0
            this._voteCloseLong = 0
            this._voteCloseShort = 0

            this._voteLongAmount = 0.0
            this._voteShortAmount = 0.0
            this._voteHoldAmount = 0.0
            this._voteCloseLongAmount = 0.0
            this._voteCloseShortAmount = 0.0

            #final expenditure after votes are tallied
            this._targetOrderPercent = 0.0

            try:                
                this.returns = data[this.parent.qsec].returns()
            except:
                this.framework.logger.error("{0} unable to obtain returns()  setting returns to zero  open={1}.  close = {2}".format(this.parent.qsec, this.open_price, this.close_price))
                this.returns = 0.0


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
        #this.qsec=Security.QSecurity()
        #this.qsec=None
        this.framework = framework
        this.security_start_date = datetime.datetime.utcfromtimestamp(0)
        this.security_end_date = datetime.datetime.utcfromtimestamp(0)
        this.simFrame = -1;
        this.state = []
        this.security_start_price = 0.0
        this.security_end_price = 0.0
        this.partialPositions = {}
        
        
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
        assert(this.simFrame>=0)

        
        
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

        #construct new state for this frame
        nowState = Security.State(this,this.framework)
        nowState.initializeAndPrepend(this.state, data)

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
        
        this.targetedSids = [] #array of sids (ex: "SPY" if offline, 123 if online) you wish to target.  if empty, all securites returned by data are used
        this.targetedSecurities = {} #dictionary, indexed by sid. must check sec.isActive before using
        this.allSecurities = {} #dictionary of all securities, including those not targeted

        if is_offline_Zipline:
            this.logger = Shims._Logger(this)
        else:
            this.logger = log
        pass
    
    def initialize(this):
        #do init here
        if this.isOffline:
            #passed to the run method
            this._offlineZiplineData = this.initialize_loadDataOffline_DataFrames()
            #our targeted sids will be everything returned by 'data'
            #this.targetedSids = list(this._offlineZiplineData.columns.values)
        else:
            targetedQSecs = this.initialize_loadDataOnline_SecArray()
            if targetedQSecs:
                this.targetedSids = [sec.sid for sec in targetedQSecs]
            
            #this.tradingAlgorithm.logger.info(len(this.securityIds))
            #this.tradingAlgorithm.logger.info(this.securityIds)
        
        pass

    def initialize_loadDataOffline_DataFrames(this):
        '''return a pandas dataframes of securities, ex: using the zipline.utils.factory.load_from_yahoo method
        these will be indexed in .securityId's for you to lookup in your abstract_handle_data(data)'''
        return pandas.DataFrame()
        pass
    def initialize_loadDataOnline_SecArray(this):
        '''return an array of securities, ex: [sid(123)]
        these will be indexed in .securityId's for you to lookup in your abstract_handle_data(data)
        return an empty array or none to target all securities found in data.  (good for using the set_universe)
        '''
        return []
        pass



    def initialize_first_update(this,data):
        '''called the first timestep, before update'''
        pass

    def _update_start(this,data):
        '''invoked by the tradingAlgorithm shim every update.  internally we will call abstract_update_timestep_handle_data()
        Override this, but call the super first!!!!
        '''


        this.simFrame+=1        
        #this.targetedSecurities.clear()
        this.data = data


        this.__updateSecurities(data)
        

        if not this.__isFirstTimestepRun:
            this.__isFirstTimestepRun=True
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
                sid = qsec;
                qsec = data[qsec]
            currentQSecs[sid]=qsec
            #determine new securities found in data
            if not this.allSecurities.has_key(sid):
                newQSecs[sid]=qsec


        #construct new Security objects for our newQSecs
        for sid, qsec in newQSecs.items():
            newSecurity = Security(sid,this)
            assert(not this.targetedSecurities.has_key(sid))
            assert(not this.allSecurities.has_key(sid))
            this.allSecurities[sid]=newSecurity
            #add it to targeted collection if we need to 
            if len(this.targetedSids)==0 or sid in this.targetedSids:
                this.targetedSecurities[sid]=newSecurity
        newQSecs.clear()


        #update all security objects, giving a null qsec if one doesn't exist in our data dictionary
        for sid, security in this.allSecurities.items():
            qsec = currentQSecs.get(sid)
            security.update(qsec, data)
        

    def get_datetime(this):
        if is_offline_Zipline:
            if len(this.targetedSecurities)==0:
                return datetime.datetime.fromtimestamp(0,pytz.UTC)
            else:
                return this.targetedSecurities.values()[0].datetime
        else:
            return get_datetime()
        pass

#entrypoints



def initalize_zipline():
    '''initialize method run when using zipline'''
    
    tradingAlgorithm = Shims._TradingAlgorithm_ZiplineShim()
    context = tradingAlgorithm.context;
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
    #if you need set universe, do it here
    set_universe(universe.DollarVolumeUniverse(floor_percentile=99.5,ceiling_percentile=100.0))

##############  CROSS PLATFORM USERCODE BELOW.   EDIT BELOW THIS LINE
##############  CROSS PLATFORM USERCODE BELOW.   EDIT BELOW THIS LINE
##############  CROSS PLATFORM USERCODE BELOW.   EDIT BELOW THIS LINE

class StandardTechnicalIndicators(FrameStateBase):

    def initialize(this, data):
        
        #predefine for intelisence
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

        pass

class FollowMarketStrategy(FrameStateBase):
    def initialize(this, data):
        #partialPositions
        this.parialPosition = this.parent.partialPositions["followMarketStrategy"]

        security = this.parent
        
        #simple "follow market" example
        if security.state[0].close_price < security.standardIndicators[0].mavg7 and security.standardIndicators[0].mavg7 < security.standardIndicators[0].mavg30:
            this.parialPosition.targetCapitalSharePercent = 1.0
        elif security.state[0].close_price > security.standardIndicators[0].mavg7 and security.standardIndicators[0].mavg7 > security.standardIndicators[0].mavg30:
            this.parialPosition.targetCapitalSharePercent = -1.0
        else:
            this.parialPosition.targetCapitalSharePercent = 0.0

        pass


class ExampleAlgo(FrameworkBase):
    def initialize_loadDataOffline_DataFrames(this):
        '''only called when offline (zipline)
        note that i dropped offline zipline support due to it's differences/defects so you'll have to get it working again yourself'''
        # Load data
        start = datetime.datetime(2002, 1, 4, 0, 0, 0, 0, pytz.utc)
        end = datetime.datetime(2002, 3, 1, 0, 0, 0, 0, pytz.utc)
        data = zipline.utils.factory.load_from_yahoo(stocks=['SPY', 'XLY'], indexes={}, start=start,
                           end=end, adjusted=False)
        return data
        pass
    def initialize_loadDataOnline_SecArray(this):
        '''only called when online (quantopian)'''
        qsecs = [
                sid(8554), # SPY S&P 500
                ]
        #if we return an array of qsecs, our framework will ignore any additional securities found in data
        return qsecs 
    
    def initialize_first_update(this, data):
        this.knownSecurities = {}

    def update(this, data):
        ''' order 1 share of the first security each timestep'''  
        
        ##PHASE 1: let framework init new securities, determine active.
        activeSecurities = {}
        for sid,security in this.targetedSecurities.items():
            if not this.knownSecurities.has_key(sid):
                this.knownSecurities[sid]=security
                #new, so do our framework's custom init logic on this security
                this.__initializeSecurity(security,data)

            if not security.isActive:
                continue
            activeSecurities[sid]=security
        
        for sid,security in activeSecurities.items():
            ##PHASE 2: update technical indicators for ALL active securities found
            this.__update_technicalIndicators(security,data)
       
        for sid,security in this.targetedSecurities.items():
            #PHASE 3: update algorithms for targetedSecurities
            this.__update_algorithms(security,data)

           
        for sid,security in this.targetedSecurities.items():
            ##PHASE 4: process orders for targetedSecurities     
            this.__update_orders(security,data)
            

    def __initializeSecurity(this,security,data):
        '''do our framework's custom init logic on this security'''
        security.standardIndicators = []

        security.followMarketStrategy = []
        security.partialPositions["followMarketStrategy"] = PartialPosition(security)

        pass

    def __update_technicalIndicators(this,security,data):
        '''##PHASE 2: update technical indicators for ALL active securities found'''
        frameStdInd = StandardTechnicalIndicators(security,this)
        frameStdInd.initializeAndPrepend(security.standardIndicators, data)
        assert(frameStdInd == security.standardIndicators[0])

        pass
    def __update_algorithms(this,security,data):
        '''#PHASE 3: update algorithms for targetedSecurities'''

        followMarketStrategy = FollowMarketStrategy(security,this)
        followMarketStrategy.initializeAndPrepend(security.followMarketStrategy,data)

        pass
    def __update_orders(this,security,data):    
        '''##PHASE 4: process orders for targetedSecurities     '''  

        security.update_orders_phase4(data)

##############  CONFIGURATION BELOW

def constructFramework(context,isOffline):
    '''factory method to return your custom framework/trading algo'''
    return ExampleAlgo(context,isOffline);

############## OFLINE RUNNER BELOW.  EDIT ABOVE THIS LINE
############## OFLINE RUNNER BELOW.  EDIT ABOVE THIS LINE
############## OFLINE RUNNER BELOW.  EDIT ABOVE THIS LINE

is_offline_Zipline = False
if __name__ == '__main__':  
    is_offline_Zipline = True
    initalize_zipline() #obsolete, this framework doesn't work with zipline anymore
