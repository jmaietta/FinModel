"""
Base configuration module for the SEC EDGAR Parser.
"""
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Union


@dataclass
class ApiConfig:
    """Configuration for API access."""
    base_url: str
    api_key: Optional[str] = None
    rate_limit: int = 10  # requests per second
    timeout: int = 30  # seconds
    max_retries: int = 3


@dataclass
class ParserConfig:
    """Configuration for the parser."""
    cache_dir: str
    output_dir: str
    log_level: str = "INFO"
    max_workers: int = 4
    validate_output: bool = True


class Config:
    """Main configuration class for the SEC EDGAR Parser."""
    
    # Default SEC EDGAR API endpoints
    SEC_EDGAR_SUBMISSIONS_URL = "https://data.sec.gov/submissions"
    SEC_EDGAR_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts"
    SEC_EDGAR_COMPANY_CONCEPT_URL = "https://data.sec.gov/api/xbrl/companyconcept"
    
    # SIC codes for Technology sector
    TECH_SIC_CODES = [
        # Computer Hardware
        3570, 3571, 3572, 3575, 3576, 3577, 3578, 3579,
        # Computer Software
        7370, 7371, 7372, 7373, 7374, 7375, 7376, 7377, 7378, 7379,
        # Semiconductors
        3674,
        # Communications Equipment
        3661, 3663, 3669,
        # Electronics
        3670, 3671, 3672, 3673, 3675, 3676, 3677, 3678, 3679,
        # Internet Services
        7370, 7371, 7372, 7373, 7374, 7375, 7376, 7377, 7378, 7379
    ]
    
    # Income statement taxonomy elements (US GAAP)
    INCOME_STMT_ELEMENTS = [
        # Revenue items
        "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", 
        "SalesRevenueNet", "SalesRevenueGoodsNet",
        # Cost items
        "CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold",
        # Gross profit
        "GrossProfit",
        # Operating expenses
        "OperatingExpenses", "ResearchAndDevelopmentExpense", 
        "SellingGeneralAndAdministrativeExpense", "SellingAndMarketingExpense",
        # Operating income
        "OperatingIncomeLoss",
        # Other income/expenses
        "NonoperatingIncomeExpense", "InterestExpense", "InterestIncome",
        # Income before taxes
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        # Income taxes
        "IncomeTaxExpenseBenefit",
        # Net income
        "NetIncomeLoss", "NetIncomeLossAvailableToCommonStockholdersBasic",
        # Earnings per share
        "EarningsPerShareBasic", "EarningsPerShareDiluted"
    ]
    
    # Tech-specific income statement elements
    TECH_SPECIFIC_ELEMENTS = [
        "SubscriptionRevenue", "CloudServicesRevenue", "LicenseRevenue",
        "ProfessionalServicesRevenue", "HardwareRevenue", "AdvertisingRevenue",
        "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
        "StockBasedCompensation"
    ]
    
    def __init__(self, 
                 api_config: Optional[ApiConfig] = None,
                 parser_config: Optional[ParserConfig] = None):
        """Initialize configuration with optional overrides."""
        self.api = api_config or self._default_api_config()
        self.parser = parser_config or self._default_parser_config()
    
    @staticmethod
    def _default_api_config() -> ApiConfig:
        """Create default API configuration."""
        return ApiConfig(
            base_url="https://data.sec.gov",
            api_key=os.environ.get("SEC_API_KEY"),
            rate_limit=10,
            timeout=30,
            max_retries=3
        )
    
    @staticmethod
    def _default_parser_config() -> ParserConfig:
        """Create default parser configuration."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return ParserConfig(
            cache_dir=os.path.join(base_dir, "data", "cache"),
            output_dir=os.path.join(base_dir, "data", "output"),
            log_level="INFO",
            max_workers=4,
            validate_output=True
        )
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'Config':
        """Create configuration from dictionary."""
        api_config = ApiConfig(**config_dict.get("api", {}))
        parser_config = ParserConfig(**config_dict.get("parser", {}))
        return cls(api_config=api_config, parser_config=parser_config)
    
    @classmethod
    def from_file(cls, file_path: str) -> 'Config':
        """Load configuration from file."""
        import json
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {
            "api": {
                "base_url": self.api.base_url,
                "api_key": self.api.api_key,
                "rate_limit": self.api.rate_limit,
                "timeout": self.api.timeout,
                "max_retries": self.api.max_retries
            },
            "parser": {
                "cache_dir": self.parser.cache_dir,
                "output_dir": self.parser.output_dir,
                "log_level": self.parser.log_level,
                "max_workers": self.parser.max_workers,
                "validate_output": self.parser.validate_output
            }
        }
    
    def save(self, file_path: str) -> None:
        """Save configuration to file."""
        import json
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
