#!/usr/bin/env python3
"""
Alpaca functionality to implement the generic interface components defined
by the metaclass.

Module Attributes:
  N/A

(C) Copyright 2020 Jonathan Casey.  All Rights Reserved Worldwide.
"""
import logging

import alpaca_trade_api as tradeapi

from grand_trade_auto.broker import broker_meta
from grand_trade_auto.general import config



logger = logging.getLogger(__name__)



class BrokerAlpaca(broker_meta.BrokerMeta):
    """
    The Alpaca broker functionality.

    Class Attributes:
      base_urls ({str:str}): The base URLs, keyed by trade domain.

    Instance Attributes:
      trade_domain (str): The domain for trading (live or paper).
      cp_broker_id (str): The id used as the section name in the broker
        conf.  Will be used for loading credentials on-demand.
      cp_secrets_id (str): The id used as the section name in the secrets
        conf.  Will be used for loading credentials on-demand.

      base_url (str): The base url to use based on trade domain.
      rest_api (REST): The cached rest API connection; or None if not connected
        and cached.
      stream_conn (StreamConn): The cached stream socket connection; or None if
        not connected and cached.
    """
    base_urls = {
        'live': 'https://api.alpaca.markets',
        'paper': 'https://paper-api.alpaca.markets',
    }



    def __init__(self, trade_domain, cp_broker_id, cp_secrets_id):
        """
        Creates the broker handle.

        Args:
          trade_domain (str): The domain for trading (live or paper).
          cp_broker_id (str): The id used as the section name in the broker
            conf.  Will be used for loading credentials on-demand.
          cp_secrets_id (str): The id used as the section name in the secrets
            conf.  Will be used for loading credentials on-demand.
        """
        self.trade_domain = trade_domain
        self.cp_broker_id = cp_broker_id
        self.cp_secrets_id = cp_secrets_id

        self.base_url = self.base_urls[trade_domain]

        self.rest_api = None
        self.stream_conn = None

        super().__init__()



    @classmethod
    def load_from_config(cls, broker_cp, broker_id, secrets_cp, secrets_id):
        """
        Loads the broker config for this broker from the configparsers
        from files provided.

        Args:
          broker_cp (configparser): The full configparser from the broker conf.
          broker_id (str): The ID name for this broker as it appears as the
            section header in the broker_cp.
          secrets_cp (configparser): The full configparser from the secrets
            conf.
          secrets_id (str): The ID name for this broker's secrets as it
            appears as the section header in the secrets_cp.

        Returns:
          broker_handle (BrokerMeta<>): The BrokerMeta<> object created and
            loaded from config, where BrokerMeta<> is a subclass of
            BrokerMeta (e.g. BrokerAlpaca).
        """
        kwargs = {}

        kwargs['trade_domain'] = broker_cp[broker_id]['trade domain']
        kwargs['cp_broker_id'] = broker_id
        kwargs['cp_secrets_id'] = secrets_id

        broker_handle = BrokerAlpaca(**kwargs)
        return broker_handle



    @classmethod
    def get_type_names(cls):
        """
        Get the list of names that can be used as the 'type' in the broker
        conf to identify this broker.

        Returns:
          ([str]): A list of names that are valid to use for this broker type.
        """
        return ['alpaca', 'apca']



    def connect(self, interface='rest'):
        """
        Connects via the desired interface.  Connection caching is handled by
        the API module.

        Args:
          interface (str): Specify whether to connect to the 'rest' API; or to
            use the 'stream' connection.

        Raises:
          (NotImplementedError): 'stream' is not yet implemented.
          (ValueError): interface is something other than 'rest', 'stream'.
          (ConnectionRefusedError): Attempted and failed to connect.
        """
        if interface == 'rest' and self.rest_api is not None:
            return
        if interface == 'stream' and self.stream_conn is not None:
            return

        broker_cp = config.read_conf_file('brokers.conf')
        secrets_cp = config.read_conf_file('.secrets.conf')

        kwargs = {
            'base_url': self.base_url,
        }
        kwargs['key_id'] = broker_cp.get(self.cp_broker_id, 'api key id',
                fallback=None)
        kwargs['key_id'] = secrets_cp.get(self.cp_secrets_id, 'api key id',
                fallback=kwargs['key_id'])
        kwargs['secret_key'] = secrets_cp.get(self.cp_secrets_id, 'secret key',
                fallback=None)

        if interface == 'rest':
            self.rest_api = tradeapi.REST(**kwargs)
            account = self.rest_api.get_account()
            if account.status == 'ACTIVE':
                logger.info('Established connection to Alpaca via REST.')
            else:
                msg = 'Unable to connect to Alpaca.' \
                        + f'  Account status: {account.status}'
                logger.critical(msg)
                raise ConnectionRefusedError(msg)

        elif interface == 'stream':
            raise NotImplementedError(
                    'Stream connection not implemented for Alpaca')
        else:
            raise ValueError('Invalid interface for Alpaca'
                    + f' -- must be "rest" or "stream"; got {interface}')
