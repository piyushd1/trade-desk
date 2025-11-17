"""
Technical Analysis Service

Computes technical indicators from historical OHLCV data using the 'ta' library.
Supports all indicators available in the ta library: momentum, volume, volatility, trend, and others.
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.services.zerodha_data_service import query_historical_data

logger = logging.getLogger(__name__)


class TechnicalAnalysisService:
    """
    Service for computing technical indicators from stored historical data.
    
    All indicators are computed at runtime from stored OHLCV data.
    No pre-computation or storage of indicator values.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_ohlcv_dataframe(
        self,
        instrument_token: int,
        interval: str = "day",
        limit: int = 500,
        start: Optional[pd.Timestamp] = None,
        end: Optional[pd.Timestamp] = None,
    ) -> pd.DataFrame:
        """
        Fetch historical candles and convert to pandas DataFrame.
        
        Args:
            instrument_token: Zerodha instrument token
            interval: Time interval (minute, 5minute, day, etc.)
            limit: Maximum number of candles to fetch
            start: Optional start timestamp
            end: Optional end timestamp
        
        Returns:
            DataFrame with columns: ['open', 'high', 'low', 'close', 'volume', 'oi']
            Index: DatetimeIndex (timestamp)
        """
        candles = await query_historical_data(
            self.db,
            instrument_token=instrument_token,
            interval=interval,
            start=start,
            end=end,
            limit=limit,
        )
        
        if not candles:
            logger.warning(f"No historical data found for instrument {instrument_token}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Ensure numeric columns
        for col in ['open', 'high', 'low', 'close', 'volume', 'oi']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        logger.info(f"Loaded {len(df)} candles for instrument {instrument_token}")
        return df[['open', 'high', 'low', 'close', 'volume', 'oi']]
    
    async def compute_indicators(
        self,
        instrument_token: int,
        interval: str = "day",
        indicators: Optional[List[str]] = None,
        limit: int = 500,
        **indicator_params: Dict[str, Any],
    ) -> pd.DataFrame:
        """
        Compute technical indicators for an instrument.
        
        Args:
            instrument_token: Zerodha instrument token
            interval: Time interval (minute, 5minute, day, etc.)
            indicators: List of indicator names to compute. If None, computes all.
            limit: Maximum number of candles to fetch
            **indicator_params: Custom parameters for indicators (e.g., sma_periods=[20, 50])
        
        Returns:
            DataFrame with OHLCV data + computed indicators
        """
        # Fetch OHLCV data
        df = await self.get_ohlcv_dataframe(
            instrument_token=instrument_token,
            interval=interval,
            limit=limit,
        )
        
        if df.empty:
            logger.warning(f"No data available for computing indicators")
            return df
        
        # Compute indicators
        if indicators is None:
            # Compute all indicators
            df = self._compute_all_indicators(df, **indicator_params)
        else:
            # Compute selected indicators
            df = self._compute_selected_indicators(df, indicators, **indicator_params)
        
        logger.info(f"Computed {len(df.columns) - 6} indicators for instrument {instrument_token}")
        return df
    
    def _compute_all_indicators(
        self,
        df: pd.DataFrame,
        **params: Dict[str, Any],
    ) -> pd.DataFrame:
        """Compute all available technical indicators."""
        try:
            import ta
        except ImportError:
            logger.error("ta library not installed. Run: pip install ta")
            return df
        
        # Momentum Indicators
        try:
            df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
            df['roc'] = ta.momentum.ROCIndicator(df['close']).roc()
            df['awesome_oscillator'] = ta.momentum.AwesomeOscillatorIndicator(
                df['high'], df['low']
            ).awesome_oscillator()
            df['kama'] = ta.momentum.KAMAIndicator(df['close']).kama()
            
            # PPO
            ppo = ta.momentum.PercentagePriceOscillator(df['close'])
            df['ppo'] = ppo.ppo()
            df['ppo_signal'] = ppo.ppo_signal()
            df['ppo_hist'] = ppo.ppo_hist()
            
            # PVO
            pvo = ta.momentum.PercentageVolumeOscillator(df['volume'])
            df['pvo'] = pvo.pvo()
            df['pvo_signal'] = pvo.pvo_signal()
            df['pvo_hist'] = pvo.pvo_hist()
            
            # Stochastic
            stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
            df['stoch'] = stoch.stoch()
            df['stoch_signal'] = stoch.stoch_signal()
            
            # TSI
            tsi = ta.momentum.TSIIndicator(df['close'])
            df['tsi'] = tsi.tsi()
            
            # Ultimate Oscillator
            df['ultimate_oscillator'] = ta.momentum.UltimateOscillator(
                df['high'], df['low'], df['close']
            ).ultimate_oscillator()
            
            # Williams %R
            df['williams_r'] = ta.momentum.WilliamsRIndicator(
                df['high'], df['low'], df['close']
            ).williams_r()
            
            logger.info("Computed momentum indicators")
        except Exception as e:
            logger.error(f"Error computing momentum indicators: {e}")
        
        # Volume Indicators
        try:
            df['ad'] = ta.volume.AccDistIndexIndicator(
                df['high'], df['low'], df['close'], df['volume']
            ).acc_dist_index()
            df['cmf'] = ta.volume.ChaikinMoneyFlowIndicator(
                df['high'], df['low'], df['close'], df['volume']
            ).chaikin_money_flow()
            df['fi'] = ta.volume.ForceIndexIndicator(
                df['close'], df['volume']
            ).force_index()
            df['eom'] = ta.volume.EaseOfMovementIndicator(
                df['high'], df['low'], df['volume']
            ).ease_of_movement()
            df['vwap'] = ta.volume.VolumeWeightedAveragePrice(
                df['high'], df['low'], df['close'], df['volume']
            ).volume_weighted_average_price()
            df['mfi'] = ta.volume.MFIIndicator(
                df['high'], df['low'], df['close'], df['volume']
            ).money_flow_index()
            df['nvi'] = ta.volume.NegativeVolumeIndexIndicator(
                df['close'], df['volume']
            ).negative_volume_index()
            df['obv'] = ta.volume.OnBalanceVolumeIndicator(
                df['close'], df['volume']
            ).on_balance_volume()
            
            logger.info("Computed volume indicators")
        except Exception as e:
            logger.error(f"Error computing volume indicators: {e}")
        
        # Volatility Indicators
        try:
            df['atr'] = ta.volatility.AverageTrueRange(
                df['high'], df['low'], df['close']
            ).average_true_range()
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['close'])
            df['bb_high'] = bb.bollinger_hband()
            df['bb_low'] = bb.bollinger_lband()
            df['bb_mid'] = bb.bollinger_mavg()
            df['bb_width'] = bb.bollinger_wband()
            df['bb_pct'] = bb.bollinger_pband()
            
            # Keltner Channel
            kc = ta.volatility.KeltnerChannel(df['high'], df['low'], df['close'])
            df['kc_high'] = kc.keltner_channel_hband()
            df['kc_low'] = kc.keltner_channel_lband()
            df['kc_mid'] = kc.keltner_channel_mband()
            df['kc_width'] = kc.keltner_channel_wband()
            df['kc_pct'] = kc.keltner_channel_pband()
            
            # Donchian Channel
            dc = ta.volatility.DonchianChannel(df['high'], df['low'], df['close'])
            df['dc_high'] = dc.donchian_channel_hband()
            df['dc_low'] = dc.donchian_channel_lband()
            df['dc_mid'] = dc.donchian_channel_mband()
            df['dc_width'] = dc.donchian_channel_wband()
            df['dc_pct'] = dc.donchian_channel_pband()
            
            # Ulcer Index
            df['ulcer_index'] = ta.volatility.UlcerIndex(df['close']).ulcer_index()
            
            logger.info("Computed volatility indicators")
        except Exception as e:
            logger.error(f"Error computing volatility indicators: {e}")
        
        # Trend Indicators
        try:
            # Moving Averages
            df['sma_20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
            df['sma_50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
            df['sma_200'] = ta.trend.SMAIndicator(df['close'], window=200).sma_indicator()
            df['ema_12'] = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator()
            df['ema_26'] = ta.trend.EMAIndicator(df['close'], window=26).ema_indicator()
            df['wma_9'] = ta.trend.WMAIndicator(df['close'], window=9).wma_indicator()
            
            # MACD
            macd = ta.trend.MACD(df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_diff'] = macd.macd_diff()
            
            # ADX
            adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
            df['adx'] = adx.adx()
            df['adx_pos'] = adx.adx_pos()
            df['adx_neg'] = adx.adx_neg()
            
            # Aroon
            aroon = ta.trend.AroonIndicator(df['high'], df['low'])
            df['aroon_up'] = aroon.aroon_up()
            df['aroon_down'] = aroon.aroon_down()
            df['aroon_indicator'] = aroon.aroon_indicator()
            
            # CCI
            df['cci'] = ta.trend.CCIIndicator(
                df['high'], df['low'], df['close']
            ).cci()
            
            # DPO
            df['dpo'] = ta.trend.DPOIndicator(df['close']).dpo()
            
            # Ichimoku
            ichimoku = ta.trend.IchimokuIndicator(df['high'], df['low'])
            df['ichimoku_a'] = ichimoku.ichimoku_a()
            df['ichimoku_b'] = ichimoku.ichimoku_b()
            df['ichimoku_base'] = ichimoku.ichimoku_base_line()
            df['ichimoku_conversion'] = ichimoku.ichimoku_conversion_line()
            
            # KST
            kst = ta.trend.KSTIndicator(df['close'])
            df['kst'] = kst.kst()
            df['kst_signal'] = kst.kst_sig()
            df['kst_diff'] = kst.kst_diff()
            
            # Mass Index
            df['mass_index'] = ta.trend.MassIndex(
                df['high'], df['low']
            ).mass_index()
            
            # PSAR
            psar = ta.trend.PSARIndicator(df['high'], df['low'], df['close'])
            df['psar'] = psar.psar()
            df['psar_up'] = psar.psar_up()
            df['psar_down'] = psar.psar_down()
            df['psar_up_indicator'] = psar.psar_up_indicator()
            df['psar_down_indicator'] = psar.psar_down_indicator()
            
            # STC
            df['stc'] = ta.trend.STCIndicator(df['close']).stc()
            
            # TRIX
            df['trix'] = ta.trend.TRIXIndicator(df['close']).trix()
            
            # Vortex
            vortex = ta.trend.VortexIndicator(df['high'], df['low'], df['close'])
            df['vortex_pos'] = vortex.vortex_indicator_pos()
            df['vortex_neg'] = vortex.vortex_indicator_neg()
            df['vortex_diff'] = vortex.vortex_indicator_diff()
            
            logger.info("Computed trend indicators")
        except Exception as e:
            logger.error(f"Error computing trend indicators: {e}")
        
        # Other Indicators
        try:
            df['daily_return'] = ta.others.DailyReturnIndicator(df['close']).daily_return()
            df['daily_log_return'] = ta.others.DailyLogReturnIndicator(df['close']).daily_log_return()
            df['cumulative_return'] = ta.others.CumulativeReturnIndicator(df['close']).cumulative_return()
            
            logger.info("Computed other indicators")
        except Exception as e:
            logger.error(f"Error computing other indicators: {e}")
        
        return df
    
    def _compute_selected_indicators(
        self,
        df: pd.DataFrame,
        indicators: List[str],
        **params: Dict[str, Any],
    ) -> pd.DataFrame:
        """Compute only selected indicators."""
        try:
            import ta
        except ImportError:
            logger.error("ta library not installed. Run: pip install ta")
            return df
        
        # Map of indicator names to computation functions
        for indicator in indicators:
            try:
                if indicator == 'rsi':
                    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
                
                elif indicator == 'roc':
                    df['roc'] = ta.momentum.ROCIndicator(df['close']).roc()
                
                elif indicator == 'awesome_oscillator':
                    df['awesome_oscillator'] = ta.momentum.AwesomeOscillatorIndicator(
                        df['high'], df['low']
                    ).awesome_oscillator()
                
                elif indicator == 'kama':
                    df['kama'] = ta.momentum.KAMAIndicator(df['close']).kama()
                
                elif indicator == 'ppo':
                    ppo = ta.momentum.PercentagePriceOscillator(df['close'])
                    df['ppo'] = ppo.ppo()
                    df['ppo_signal'] = ppo.ppo_signal()
                    df['ppo_hist'] = ppo.ppo_hist()
                
                elif indicator == 'stochastic':
                    stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
                    df['stoch'] = stoch.stoch()
                    df['stoch_signal'] = stoch.stoch_signal()
                
                elif indicator == 'williams_r':
                    df['williams_r'] = ta.momentum.WilliamsRIndicator(
                        df['high'], df['low'], df['close']
                    ).williams_r()
                
                elif indicator == 'ad':
                    df['ad'] = ta.volume.AccDistIndexIndicator(
                        df['high'], df['low'], df['close'], df['volume']
                    ).acc_dist_index()
                
                elif indicator == 'cmf':
                    df['cmf'] = ta.volume.ChaikinMoneyFlowIndicator(
                        df['high'], df['low'], df['close'], df['volume']
                    ).chaikin_money_flow()
                
                elif indicator == 'vwap':
                    df['vwap'] = ta.volume.VolumeWeightedAveragePrice(
                        df['high'], df['low'], df['close'], df['volume']
                    ).volume_weighted_average_price()
                
                elif indicator == 'mfi':
                    df['mfi'] = ta.volume.MFIIndicator(
                        df['high'], df['low'], df['close'], df['volume']
                    ).money_flow_index()
                
                elif indicator == 'obv':
                    df['obv'] = ta.volume.OnBalanceVolumeIndicator(
                        df['close'], df['volume']
                    ).on_balance_volume()
                
                elif indicator == 'atr':
                    df['atr'] = ta.volatility.AverageTrueRange(
                        df['high'], df['low'], df['close']
                    ).average_true_range()
                
                elif indicator == 'bollinger_bands':
                    bb = ta.volatility.BollingerBands(df['close'])
                    df['bb_high'] = bb.bollinger_hband()
                    df['bb_mid'] = bb.bollinger_mavg()
                    df['bb_low'] = bb.bollinger_lband()
                    df['bb_width'] = bb.bollinger_wband()
                    df['bb_pct'] = bb.bollinger_pband()
                
                elif indicator == 'keltner_channel':
                    kc = ta.volatility.KeltnerChannel(df['high'], df['low'], df['close'])
                    df['kc_high'] = kc.keltner_channel_hband()
                    df['kc_low'] = kc.keltner_channel_lband()
                    df['kc_mid'] = kc.keltner_channel_mband()
                
                elif indicator == 'donchian_channel':
                    dc = ta.volatility.DonchianChannel(df['high'], df['low'], df['close'])
                    df['dc_high'] = dc.donchian_channel_hband()
                    df['dc_low'] = dc.donchian_channel_lband()
                    df['dc_mid'] = dc.donchian_channel_mband()
                
                elif indicator == 'sma':
                    periods = params.get('sma_periods', [20, 50, 200])
                    for period in periods:
                        df[f'sma_{period}'] = ta.trend.SMAIndicator(
                            df['close'], window=period
                        ).sma_indicator()
                
                elif indicator == 'ema':
                    periods = params.get('ema_periods', [12, 26])
                    for period in periods:
                        df[f'ema_{period}'] = ta.trend.EMAIndicator(
                            df['close'], window=period
                        ).ema_indicator()
                
                elif indicator == 'wma':
                    periods = params.get('wma_periods', [9])
                    for period in periods:
                        df[f'wma_{period}'] = ta.trend.WMAIndicator(
                            df['close'], window=period
                        ).wma_indicator()
                
                elif indicator == 'macd':
                    macd = ta.trend.MACD(df['close'])
                    df['macd'] = macd.macd()
                    df['macd_signal'] = macd.macd_signal()
                    df['macd_diff'] = macd.macd_diff()
                
                elif indicator == 'adx':
                    adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
                    df['adx'] = adx.adx()
                    df['adx_pos'] = adx.adx_pos()
                    df['adx_neg'] = adx.adx_neg()
                
                elif indicator == 'aroon':
                    aroon = ta.trend.AroonIndicator(df['high'], df['low'])
                    df['aroon_up'] = aroon.aroon_up()
                    df['aroon_down'] = aroon.aroon_down()
                
                elif indicator == 'cci':
                    df['cci'] = ta.trend.CCIIndicator(
                        df['high'], df['low'], df['close']
                    ).cci()
                
                elif indicator == 'ichimoku':
                    ichimoku = ta.trend.IchimokuIndicator(df['high'], df['low'])
                    df['ichimoku_a'] = ichimoku.ichimoku_a()
                    df['ichimoku_b'] = ichimoku.ichimoku_b()
                    df['ichimoku_base'] = ichimoku.ichimoku_base_line()
                    df['ichimoku_conversion'] = ichimoku.ichimoku_conversion_line()
                
                elif indicator == 'psar':
                    psar = ta.trend.PSARIndicator(df['high'], df['low'], df['close'])
                    df['psar'] = psar.psar()
                    df['psar_up'] = psar.psar_up()
                    df['psar_down'] = psar.psar_down()
                
                elif indicator == 'vortex':
                    vortex = ta.trend.VortexIndicator(df['high'], df['low'], df['close'])
                    df['vortex_pos'] = vortex.vortex_indicator_pos()
                    df['vortex_neg'] = vortex.vortex_indicator_neg()
                
                elif indicator == 'daily_return':
                    df['daily_return'] = ta.others.DailyReturnIndicator(df['close']).daily_return()
                
                elif indicator == 'cumulative_return':
                    df['cumulative_return'] = ta.others.CumulativeReturnIndicator(df['close']).cumulative_return()
                
                else:
                    logger.warning(f"Unknown indicator: {indicator}")
                
            except Exception as e:
                logger.error(f"Error computing indicator '{indicator}': {e}")
        
        return df

