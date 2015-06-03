# -*- encoding: utf-8 -*-

import copy

from decimal import Decimal, ROUND_HALF_EVEN

import pytest  # Works with less code, more consistency than unittest.
import moneyed

from moneyed.classes import Currency, Money, MultiMoney, MoneyComparisonError, CURRENCIES, DEFAULT_CURRENCY
from moneyed.localization import format_money, _sign, _format


class TestCurrency:

    def setup_method(self, method):
        self.default_curr_code = 'BTC'
        self.default_curr = CURRENCIES[self.default_curr_code]

    def test_init(self):
        usd_countries = CURRENCIES['USD'].countries
        US_dollars = Currency(
            code='USD',
            numeric='840',
            name='US Dollar',
            countries=['AMERICAN SAMOA',
                       'BRITISH INDIAN OCEAN TERRITORY',
                       'ECUADOR',
                       'GUAM',
                       'MARSHALL ISLANDS',
                       'MICRONESIA',
                       'NORTHERN MARIANA ISLANDS',
                       'PALAU',
                       'PUERTO RICO',
                       'TIMOR-LESTE',
                       'TURKS AND CAICOS ISLANDS',
                       'UNITED STATES',
                       'UNITED STATES MINOR OUTLYING ISLANDS',
                       'VIRGIN ISLANDS (BRITISH)',
                       'VIRGIN ISLANDS (U.S.)'])
        assert US_dollars.code == 'USD'
        assert US_dollars.countries == usd_countries
        assert US_dollars.name == 'US Dollar'
        assert US_dollars.numeric == '840'

    def test_repr(self):
        assert str(self.default_curr) == self.default_curr_code


class TestMoney:

    def setup_method(self, method):
        self.one_million_decimal = Decimal('1000000')
        self.USD = CURRENCIES['USD']
        self.one_million_bucks = Money(amount=self.one_million_decimal,
                                       currency=self.USD)

        self.EUR = CURRENCIES['EUR']
        self.one_million_euros = Money(amount=self.one_million_decimal,
                                       currency=self.EUR)

    def test_init(self):
        one_million_dollars = Money(amount=self.one_million_decimal,
                                    currency=self.USD)
        assert one_million_dollars.amount == self.one_million_decimal
        assert one_million_dollars.currency == self.USD

    def test_init_string_currency_code(self):
        one_million_dollars = Money(amount=self.one_million_decimal,
                                    currency='usd')
        assert one_million_dollars.amount == self.one_million_decimal
        assert one_million_dollars.currency == self.USD

    def test_init_default_currency(self):
        one_million = self.one_million_decimal
        one_million_dollars = Money(amount=one_million)  # No currency given!
        assert one_million_dollars.amount == one_million
        assert one_million_dollars.currency == DEFAULT_CURRENCY

    def test_init_float(self):
        one_million_dollars = Money(amount=1000000.0)
        assert one_million_dollars.amount == self.one_million_decimal

    def test_repr(self):
        assert repr(self.one_million_bucks) == '1000000 USD'
        assert repr(Money(Decimal('2.000'), 'PLN')) == '2 PLN'
        m_1 = Money(Decimal('2.000'), 'PLN')
        m_2 = Money(Decimal('2.000000'), 'PLN')
        assert repr(m_1) == repr(m_2)

    def test_str(self):
        assert str(self.one_million_bucks) == 'US$1,000,000.00'

    def test_format_money(self):
        # Two decimal places by default
        assert format_money(self.one_million_bucks) == 'US$1,000,000.00'
        # No decimal point without fractional part
        assert format_money(self.one_million_bucks, decimal_places=0) == 'US$1,000,000'
        # locale == pl_PL
        one_million_pln = Money('1000000', 'PLN')
        # Two decimal places by default
        assert format_money(one_million_pln, locale='pl_PL') == '1 000 000,00 zł'

        # overriden sign/format locale display default sign with locale group parameter
        assert format_money(self.one_million_bucks, locale='pl_PL') == 'US$1 000 000,00'
        # non overriden sign/format locale display default money sign with default group parameter
        assert format_money(self.one_million_bucks, locale='fr_FR') == 'US$1,000,000.00'

        # No decimal point without fractional part
        assert format_money(one_million_pln, locale='pl_PL', decimal_places=0) == '1 000 000 zł'

        # add different sign for money USD in locale pl_PL
        _sign('pl_PL', moneyed.USD, prefix='$')
        assert format_money(self.one_million_bucks, locale='pl_PL') == '$1 000 000,00'

        # default locale display correct money sign with default group parameter
        assert format_money(self.one_million_euros) == '1,000,000.00 €'
        # non overriden sign/format locale display default money sign with default group parameter
        assert format_money(self.one_million_euros, locale='fr_FR') == '1,000,000.00 €'
        # overriden sign/locale locale display default money sign with locale group parameter
        assert format_money(self.one_million_euros, locale='en_US') == '1,000,000.00 €'

        # add format for fr_FR locale
        _format("fr_FR", group_size=3, group_separator=" ", decimal_point=",",
                positive_sign="", trailing_positive_sign="",
                negative_sign="-", trailing_negative_sign="",
                rounding_method=ROUND_HALF_EVEN)
        # overriden format locale display correct sign with locale group parameter
        assert format_money(self.one_million_euros, locale='fr_FR') == '1 000 000,00 €'

    def test_add(self):
        assert (self.one_million_bucks + self.one_million_bucks
                == Money(amount='2000000', currency=self.USD))

    def test_sub(self):
        zeroed_test = self.one_million_bucks - self.one_million_bucks
        assert zeroed_test == Money(amount=0, currency=self.USD)

    def test_mul(self):
        x = Money(amount=111.33, currency=self.USD)
        assert 3 * x == Money(333.99, currency=self.USD)
        assert Money(333.99, currency=self.USD) == 3 * x

    def test_div(self):
        x = Money(amount=50, currency=self.USD)
        y = Money(amount=2, currency=self.USD)
        assert x / y == Decimal(25)

    def test_div_by_non_Money(self):
        x = Money(amount=50, currency=self.USD)
        y = 2
        assert x / y == Money(amount=25, currency=self.USD)

    def test_rmod(self):
        assert 1 % self.one_million_bucks == Money(amount=10000,
                                                   currency=self.USD)

    def test_rmod_bad(self):
        with pytest.raises(TypeError):
            assert (self.one_million_bucks % self.one_million_bucks
                    == 1)

    def test_convert_to_default(self):
        # Currency conversions are not implemented as of 2/2011; when
        # they are working, then convert_to_default and convert_to
        # will need to be tested.
        pass

    # Note: no tests for __eq__ as it's quite thoroughly covered in
    # the assert comparisons throughout these tests.

    def test_ne(self):
        x = Money(amount=1, currency=self.USD)
        assert self.one_million_bucks != x

    def test_equality_to_other_types(self):
        # x = Money(amount=1, currency=self.USD)
        assert self.one_million_bucks is not None
        assert self.one_million_bucks != {}

    def test_lt(self):
        x = Money(amount=1, currency=self.USD)
        assert x < self.one_million_bucks

    def test_gt(self):
        x = Money(amount=1, currency=self.USD)
        assert self.one_million_bucks > x

    def test_gt_mistyped(self):
        x = 1.0
        with pytest.raises(MoneyComparisonError):
            assert self.one_million_bucks > x

    def test_abs(self):
        abs_money = Money(amount=1, currency=self.USD)
        x = Money(amount=-1, currency=self.USD)
        assert abs(x) == abs_money
        # y = Money(amount=1, currency=self.USD)
        assert abs(x) == abs_money


class TestMultiMoney:
    def setup_method(self, method):
        self.one_million_decimal = Decimal('1000000')
        self.USD = CURRENCIES['USD']
        self.one_million_bucks = Money(amount=self.one_million_decimal,
                                       currency=self.USD)

        self.one_thousand_decimal = Decimal('1000')
        self.BTC = CURRENCIES['BTC']
        self.one_thousand_bitcoins = Money(amount=self.one_thousand_decimal,
                                           currency=self.BTC)

        self.one_mixed_fortune = MultiMoney(self.one_million_bucks, self.one_thousand_bitcoins)

    def test_init(self):
        assert self.one_mixed_fortune.getMoneys('USD') == self.one_million_bucks
        assert self.one_mixed_fortune.getMoneys('BTC') == self.one_thousand_bitcoins

    def test_init_empty(self):
        one_empty_piggy = MultiMoney()
        assert one_empty_piggy == 0
        assert one_empty_piggy == MultiMoney(Money())

    # def test_repr(self):
    #     assert repr(self.one_million_bucks) == '1000000 USD'
    #     assert repr(Money(Decimal('2.000'), 'PLN')) == '2 PLN'

    # def test_str(self):
    #     assert str(self.one_million_bucks) == 'US$1,000,000.00'

    def test_add(self):
        piggy = MultiMoney()
        piggy += MultiMoney(self.one_million_bucks)
        assert piggy == MultiMoney(self.one_million_bucks)

        piggy += self.one_million_bucks
        assert piggy == MultiMoney(self.one_million_bucks * 2)

        piggy += self.one_thousand_bitcoins
        assert piggy == MultiMoney(self.one_million_bucks * 2, self.one_thousand_bitcoins)

    def test_add_non_money(self):
        with pytest.raises(TypeError):
            MultiMoney() + 123

    def test_sub(self):
        piggy = copy.copy(self.one_mixed_fortune)
        piggy -= MultiMoney(self.one_million_bucks)
        assert piggy == MultiMoney(self.one_thousand_bitcoins)

        piggy -= self.one_thousand_bitcoins
        assert piggy == MultiMoney()

        piggy -= self.one_million_bucks
        assert piggy == MultiMoney(self.one_million_bucks * -1)

    def test_sub_non_money(self):
        with pytest.raises(TypeError):
            MultiMoney() - 123

    def test_mul(self):
        assert 3 * self.one_mixed_fortune == MultiMoney(self.one_million_bucks * 3, self.one_thousand_bitcoins * 3)

    def test_div(self):
        assert self.one_mixed_fortune / 3 == MultiMoney(self.one_million_bucks / 3, self.one_thousand_bitcoins / 3)

    def test_eq(self):
        piggy = MultiMoney()
        assert piggy == MultiMoney(Money(amount=0))
        assert piggy == Money(amount=0)
        assert piggy == 0

        piggy += Money(amount=1, currency='BTC')
        assert piggy == MultiMoney(Money(amount=1))
        assert piggy == Money(amount=1)
        assert piggy == 1

        piggy += Money(amount=1, currency='USD')
        assert piggy == MultiMoney(Money(amount=1), Money(amount=1, currency='USD'))
        assert piggy != Money(amount=1)
        assert piggy != 1

    def test_ne(self):
        piggy = MultiMoney()
        assert piggy != MultiMoney(Money(amount=1))
        assert piggy != Money(amount=1)
        assert piggy != 1

        piggy += Money(amount=1, currency='BTC')
        assert piggy != MultiMoney(Money(amount=2))
        assert piggy != Money(amount=2)
        assert piggy != 2

        piggy += Money(amount=1, currency='USD')
        assert piggy != MultiMoney(Money(amount=1), Money(amount=2, currency='USD'))
        assert piggy != Money(amount=1)
        assert piggy != 1

    def test_lt(self):
        one_buck_piggy = MultiMoney(Money(amount=1, currency=self.USD))
        assert one_buck_piggy < MultiMoney(self.one_million_bucks)
        assert one_buck_piggy < self.one_mixed_fortune
        one_buck_thousand_bitcoin_piggy = one_buck_piggy + self.one_thousand_bitcoins
        assert one_buck_thousand_bitcoin_piggy < self.one_mixed_fortune

        assert not MultiMoney(Money(currency='USD')) < MultiMoney()
        assert not self.one_mixed_fortune < MultiMoney()
        assert not self.one_mixed_fortune < one_buck_thousand_bitcoin_piggy
        assert not MultiMoney() < MultiMoney()
        assert not MultiMoney() < MultiMoney(Money())

    def test_gt(self):
        x = MultiMoney(Money(1, 'BTC'), Money(-1, 'USD'))
        y = MultiMoney(Money(0.5, 'BTC'))
        assert not x > y

        one_buck_piggy = MultiMoney(Money(amount=1, currency=self.USD))
        assert MultiMoney(self.one_million_bucks) > one_buck_piggy
        assert self.one_mixed_fortune > one_buck_piggy
        one_buck_thousand_bitcoin_piggy = one_buck_piggy + self.one_thousand_bitcoins
        assert self.one_mixed_fortune > one_buck_thousand_bitcoin_piggy

        assert not MultiMoney(Money(currency='USD')) > MultiMoney()
        assert not MultiMoney() > self.one_mixed_fortune
        assert not one_buck_thousand_bitcoin_piggy > self.one_mixed_fortune
        assert not MultiMoney() > MultiMoney()
        assert not MultiMoney() > MultiMoney(Money())
