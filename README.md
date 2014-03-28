QuantShim
=========

a python framework for trading financial instruments algorithmicly via quantopian.com.  

Why
===
I hate python, but it's the defacto standard for open-source quantitative trading.  
So I wanted a codebase that can use Python Tools for Visual Studio's intelisence.  So that's why I made this.

History
======
- v1
-- The first checkin is Zipline compatable.  After that it is not.
- v1.0.1
 - Add Security object to provide persistant state / logic for securities
 - Add state history to security, provide easy way for things to get their own state + history of their own state.



Roadmap
=============
- Add logic for multi-algorithm and multi-security collaboritive trading.
- focus on intraday, but make sure framework+algos can still work with interday
- infrastructure for storing history per algo-security pair




How To Install (Windows, using PythonTools for VisualStudio)
================

- install vs2013
- install pytools for vs2013
- install activestate python (32bit)
- run the following from your cmd prompt

 - pypm -g install pip
 - pypm -g install numpy
 - pypm -g install "scipy<0.10"
 - pypm -g install pytz
 - pypm -g install pandas
 - pypm -g install pyzmq
 - pypm -g install ipython
 - pypm --force -g install matplotlib
 - pypm -g install pyreadline
 - pip install zipline  

- run the .sln

how to run
==========
- on Quantopian.com, just copy-paste the contents of quantShim.py to a new quantopian algo, and backtest
- on zipline, just run quantShim.py  **IMPORTANT NOTE** Only the first checkin support zipline.  everything after that is for quantopian use only.
There are far too many differences/defects with the zipline runtime to continue it's support right now
 

work in progress (todo)
========
- add technical indicators framework
- add algorithm framework
- add security-algorithm pairs


