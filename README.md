QuantShim
=========

A Python framework for R&D of financial investment strategies, and trading them algorithmiclly via Quantopian.com


Features
========
- Detailed order logging
- WorstSpreadSlippage to simulate pessimistic yet realistic order execution
- Strategy framework that's easy to extend
 - StrategyPositions: Each strategy can control it's own positions without interfering with other strategy
  - Including algorithmic stop-loss and profit-loss triggers
 - Multiple Strategies supported
- TechnicalIndicators framework that's easy to extend
 - State History stored for inspecting previous frames
 - StandardTechnicalIndicators provided as example
- Designed for coding via Python Tools for Visual Studio
 - simple copy/paste into quantopian to execute
 - intelisence for most quantopian internals
- Open Source (GPL3)

Why
===
- I want a R&D platform to implement strategies and synthetic securities easily, AND
- I wanted a codebase that can use Python Tools for Visual Studio's intelisence.  
 - So that's why I made this.

History
======
- v1.1.0 (20140616)
 - big changes to strategyPositions (add algorithmic stop-loss)
 - simplify security declaration based on Quantopian platform improvements
 - add good performing "Volatility Bias" strategy as an example
  - removed QuantopianRealMoneyStrategy example
 - add Bollinger Band and Daily Indicators (not enabled by default) 
- v1.0.4 (20140422)
 - add "logging" global object to framework, 
  - allows enabling/disabling of logs, 
  - adds log time (in exchange time) 
  - allows graphing records with variables as names.
 - manually compute all standard technical indicators to workaround quantopian (TALib) bug in SMA computation
- v1.0.3 (20140419)
 - cleanup / simplifying workflows and architecture 
  - removed old examples,  now 'strategy' focused
  - added QuantopianRealMoneyStrategy as an example
  - renamed classes/functions and added docs
  - added WorstSpreadSlippage and high quality order logging
- v1.0.2
 - Add logic for multi-algorithm and multi-security collaboritive trading.
  - add realistic example of multistrategy collab (followMarketStrategy and followPriorDayStrategy operating at the same time)
 - focus on intraday, but make sure framework+algos can still work with interday
 - infrastructure for storing daily history per security/algo
- v1.0.1
 - Add Security object to provide persistant state / logic for securities
 - Add state history to security, provide easy way for things to get their own state + history of their own state.
 - add multi-phase updates, allow framework to custom init securities
 - add partial positions, so that strategies can order independantly of eachother
- v1
 - The first checkin is Zipline compatable.  After that it is not.


Roadmap
=============
- ???  email me at <jasons aat novaleaf doot coom> if you want something




How To Install (Windows, using PythonTools for VisualStudio)
================

- install vs2013
- install pytools for vs2013
- install activestate python (32bit)
- run the following from your cmd prompt

	    pypm -g install pip
	    pypm -g install numpy
	    pypm -g install "scipy<0.10"
	    pypm -g install pytz
	    pypm -g install pandas
	    pypm -g install pyzmq
	    pypm -g install ipython
	    pypm --force -g install matplotlib
	    pypm -g install pyreadline
	    pip install zipline  

- run the .sln

how to run
==========
- on Quantopian.com, just copy-paste the contents of quantShim.py to a new quantopian algo, and backtest
- on zipline, just run quantShim.py  **IMPORTANT NOTE** Only the first checkin support zipline.  everything after that is for quantopian use only.
There are far too many differences/defects with the zipline runtime to continue it's support right now
 

work in progress (todo)
========
- 
- ???  email me at <jasons aat novaleaf doot coom> if you want something



