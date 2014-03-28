
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





#global constants
global true
true = 1
global false
false = 0




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
        #def __init__(this):
        #   pass    

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
            sec = this.context.framework.targetedSecurities[sid]
            #this.logger.info(sec)
            order(sec,amount,limit_price,stop_price)
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
            #this.__isInitialized = false;          
            this.context = Shims.Context()
            this.context.tradingAlgorithm = this            
            #this.context.portfolio = this.portfolio
            pass

        def handle_data(this,data):      
            this.context.portfolio = this.portfolio
            #if not this.__isInitialized:
            #    this.__isInitialized=true
            #    this.context.portfolio=this.portfolio
                
            this.context.framework.update_timestep(data)
            pass
        pass


class FrameworkBase():
    def __init__(this, context, isOffline):
        this.isOffline = isOffline
        this.context = context
        this.tradingAlgorithm = Shims._TradingAlgorithm_QuantopianShim() #prepopulate to allow intelisence
        this.tradingAlgorithm = context.tradingAlgorithm
        this.targetedSecurities = {}
        this._targetedSecurityIds=[0]        
        del this._targetedSecurityIds[:]
        if is_offline_Zipline:
            this.logger = Shims._Logger()
            this.logger.framework = this
        else:
            this.logger = log
        
        pass
    
    def initialize(this):
        #do init here
        if this.isOffline:
            #passed to the run method
            this._offlineZiplineData = this.abstract_loadDataOffline_DataFrames()
            this._targetedSecurityIds = list(this._offlineZiplineData.columns.values)
        else:
            this._targetedSecurityIds = [sec.sid for sec in this.abstract_loadDataOnline_SecArray()]
            #this.tradingAlgorithm.logger.info(len(this.securityIds))
            #this.tradingAlgorithm.logger.info(this.securityIds)
        
        pass

    def abstract_loadDataOffline_DataFrames(this):
        '''return a pandas dataframes of securities, ex: using the zipline.utils.factory.load_from_yahoo method
        these will be indexed in .securityId's for you to lookup in your abstract_handle_data(data)'''
        return pandas.DataFrame()
        pass
    def abstract_loadDataOnline_SecArray(this):
        '''return an array of securities, ex: [sid(123)]
        these will be indexed in .securityId's for you to lookup in your abstract_handle_data(data)'''
        return []
        pass

    def abstract_update_timestep_handle_data(this,data=pandas.DataFrame()):

        '''find the securities you loaded by .securityId.   
        if the security isn't present in data
        , it's temporally unavailable (not yet listed or already removed from the exchange)
        '''
        pass

    def update_timestep(this,data):
        '''invoked by the tradingAlgorithm shim every update.  internally we will call abstract_update_timestep_handle_data()'''
        this.targetedSecurities.clear()
        for qsec in data:
            
            if not this.isOffline:
                sid = qsec.sid                
            else:
                #if offline zipline, qsec is a string ex: "SPY"
                sid = qsec;
                qsec = data[qsec]

            if len(this._targetedSecurityIds)==0 or this._targetedSecurityIds.index(sid)>=0:
                this.targetedSecurities[sid]=qsec
        this.data = data
        this.abstract_update_timestep_handle_data(data)
    pass

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
def initialize(context=Shims.Context()):
    '''initialize method used when running on quantopian'''
    context.tradingAlgorithm = Shims._TradingAlgorithm_QuantopianShim()
    context.tradingAlgorithm.context = context
    context.framework = constructFramework(context,false)
    context.framework.initialize()

    pass

def handle_data(context=Shims.Context(),data=pandas.DataFrame()):    
    '''update method run every timestep on quantopian'''
    context.framework.update_timestep(data)
    
    pass

global constructFramework
def initalize_zipline():
    '''initialize method run when using zipline'''
    
    tradingAlgorithm = Shims._TradingAlgorithm_ZiplineShim()
    context = tradingAlgorithm.context;
    context.framework = constructFramework(context,true)
    context.framework.initialize()    
    tradingAlgorithm.run(context.framework._offlineZiplineData)
    pass




##############  CROSS PLATFORM USERCODE BELOW.   EDIT BELOW THIS LINE

class ExampleAlgo(FrameworkBase):
    def abstract_loadDataOffline_DataFrames(this):
        '''only called when offline (zipline)'''
        # Load data
        start = datetime.datetime(2002, 1, 4, 0, 0, 0, 0, pytz.utc)
        end = datetime.datetime(2002, 3, 1, 0, 0, 0, 0, pytz.utc)
        data = zipline.utils.factory.load_from_yahoo(stocks=['SPY', 'XLY'], indexes={}, start=start,
                           end=end, adjusted=False)
        return data
        pass
    def abstract_loadDataOnline_SecArray(this):
        '''only called when online (quantopian)'''
        return [
                sid(8554), # SPY S&P 500
                ]
        
        pass

    def abstract_update_timestep_handle_data(this, data = pandas.DataFrame()):
        ''' order 1 share of the first security each timestep'''
        if(len(this._targetedSecurityIds)>0):            
            this.logger.info("buy {0} x1".format(this._targetedSecurityIds[0]));
            this.tradingAlgorithm.order(this._targetedSecurityIds[0],1)
            pass
        else:
            this.logger.info("no security found this timestep");
    pass  

##############  CONFIGURATION BELOW

def constructFramework(context,isOffline):
    '''factory method to return your custom framework/trading algo'''
    return ExampleAlgo(context,isOffline);

############## OFLINE RUNNER BELOW.  EDIT ABOVE THIS LINE
is_offline_Zipline = false
if __name__ == '__main__':  
    #import pylab
    is_offline_Zipline = true

if(is_offline_Zipline):
    initalize_zipline()
    pass
