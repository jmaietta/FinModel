"""
Filing fetcher module for retrieving SEC filings.

This module provides functionality for locating and retrieving
SEC filings for Technology sector companies.
"""
import os
import logging
import requests
import zipfile
import io
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta
from ..api.client import ApiClient, CompanyInfo
from ..config import Config


class FilingLocator:
    """Locates SEC filings based on criteria."""
    
    def __init__(self, api_client: ApiClient, company_info: CompanyInfo):
        """Initialize filing locator.
        
        Args:
            api_client: API client for retrieving data.
            company_info: Company information utility.
        """
        self.api_client = api_client
        self.company_info = company_info
        self.logger = logging.getLogger(__name__)
    
    def find_filings(self, 
                    cik: str, 
                    form_types: List[str] = ["10-K", "10-Q", "8-K"],
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    limit: int = 100) -> List[Dict]:
        """Find filings for a company based on criteria.
        
        Args:
            cik: Central Index Key (CIK) of the company.
            form_types: List of form types to include.
            start_date: Start date for filing search.
            end_date: End date for filing search.
            limit: Maximum number of filings to return.
            
        Returns:
            List of filing metadata.
        """
        # Default date range if not specified (5 years)
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=5*365)
        
        try:
            # Get company submissions
            submissions = self.api_client.get_company_submissions(cik)
            
            if "filings" not in submissions or "recent" not in submissions["filings"]:
                self.logger.warning(f"No filings found for CIK {cik}")
                return []
            
            # Extract filing information
            filings = []
            recent_filings = submissions["filings"]["recent"]
            
            # Get the relevant arrays from the response
            form_array = recent_filings.get("form", [])
            filing_date_array = recent_filings.get("filingDate", [])
            accession_number_array = recent_filings.get("accessionNumber", [])
            primary_document_array = recent_filings.get("primaryDocument", [])
            
            # Ensure all arrays have the same length
            min_length = min(len(form_array), len(filing_date_array), 
                            len(accession_number_array), len(primary_document_array))
            
            # Process each filing
            for i in range(min_length):
                form = form_array[i]
                filing_date_str = filing_date_array[i]
                accession_number = accession_number_array[i]
                primary_document = primary_document_array[i]
                
                # Parse filing date
                filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")
                
                # Check if filing meets criteria
                if (form in form_types and 
                    start_date <= filing_date <= end_date):
                    
                    filings.append({
                        "cik": cik,
                        "form": form,
                        "filing_date": filing_date_str,
                        "accession_number": accession_number,
                        "primary_document": primary_document
                    })
                    
                    # Check if we"ve reached the limit
                    if len(filings) >= limit:
                        break
            
            return filings
            
        except Exception as e:
            self.logger.error(f"Error finding filings for CIK {cik}: {str(e)}")
            # Return empty list if API access fails
            return []
    
    def find_tech_sector_filings(self, 
                                form_types: List[str] = ["10-K", "10-Q", "8-K"],
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None,
                                limit_per_company: int = 20,
                                total_limit: int = 1000) -> List[Dict]:
        """Find filings for all Technology sector companies.
        
        Args:
            form_types: List of form types to include.
            start_date: Start date for filing search.
            end_date: End date for filing search.
            limit_per_company: Maximum number of filings per company.
            total_limit: Maximum total number of filings.
            
        Returns:
            List of filing metadata.
        """
        # Use the local mapping to get tech company CIKs
        tech_companies = []
        for ticker, info in self.company_info.ticker_to_cik_map.items():
            tech_companies.append({
                "ticker": ticker,
                "cik": str(info["cik_str"]),
                "name": info["title"]
            })
        
        all_filings = []
        
        for company in tech_companies:
            try:
                cik = company["cik"]
                
                # Find filings for this company
                company_filings = self.find_filings(
                    cik=cik,
                    form_types=form_types,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit_per_company
                )
                
                # Add company name and ticker to each filing
                for filing in company_filings:
                    filing["company_name"] = company["name"]
                    filing["ticker"] = company["ticker"]
                
                all_filings.extend(company_filings)
                
                # Check if we"ve reached the total limit
                if len(all_filings) >= total_limit:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error processing {company['name']} ({company['ticker']} - CIK: {company['cik']}): {str(e)}")
                continue
        
        return all_filings[:total_limit]


class FilingDownloader:
    """Downloads SEC filings or uses local copies if available."""
    
    def __init__(self, cache_dir: str):
        """Initialize filing downloader.
        
        Args:
            cache_dir: Directory for caching downloaded filings.
        """
        self.cache_dir = cache_dir
        self.logger = logging.getLogger(__name__)
        
        # Create cache directory if it doesn"t exist
        os.makedirs(cache_dir, exist_ok=True)
    
    def download_filing(self, 
                       cik: str, 
                       accession_number: str, 
                       filing_date: str) -> str:
        """Download a filing or use local copy and return the path.
        
        Args:
            cik: Central Index Key (CIK) of the company.
            accession_number: Accession number of the filing.
            filing_date: Filing date (YYYY-MM-DD).
            
        Returns:
            Path to the filing directory.
            
        Raises:
            Exception: If the filing cannot be downloaded or found locally.
        """
        # Format CIK and accession number
        cik_padded = cik.strip().lstrip("0").zfill(10)
        accession_formatted = accession_number.replace("-", "")
        
        # Create cache subdirectory for this filing
        filing_dir = os.path.join(self.cache_dir, cik_padded, accession_formatted)
        os.makedirs(filing_dir, exist_ok=True)
        
        # Check if filing is already cached (look for submission.txt)
        submission_path = os.path.join(filing_dir, "submission.txt")
        if os.path.exists(submission_path):
            self.logger.info(f"Using cached filing {accession_number} from {filing_dir}")
            return filing_dir
        
        # If not cached, attempt to download (this will likely fail in the current env)
        self.logger.warning(f"Filing {accession_number} not found in cache. Attempting download (may fail due to env restrictions)...")
        try:
            # Construct the URL for the complete submission file
            edgar_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession_formatted}/{accession_formatted}-index.htm"
            
            # Download the index page
            headers = {
                "User-Agent": "SecEdgarParser/1.0",
                "Accept-Encoding": "gzip, deflate",
                "Host": "www.sec.gov"
            }
            response = requests.get(edgar_url, headers=headers)
            response.raise_for_status()
            
            # Save the index page
            with open(os.path.join(filing_dir, "index.htm"), "wb") as f:
                f.write(response.content)
            
            # Download the complete submission file
            submission_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession_formatted}.txt"
            response = requests.get(submission_url, headers=headers)
            response.raise_for_status()
            
            # Save the complete submission file
            with open(submission_path, "wb") as f:
                f.write(response.content)
            
            self.logger.info(f"Successfully downloaded filing {accession_number}")
            return filing_dir
            
        except Exception as e:
            self.logger.error(f"Error downloading filing {accession_number}: {str(e)}")
            # If download fails, raise an exception indicating it needs to be provided locally
            raise Exception(f"Failed to download filing {accession_number}. Please place the filing files (submission.txt) in {filing_dir} manually.")


class FilingExtractor:
    """Extracts documents from SEC filings."""
    
    def __init__(self):
        """Initialize filing extractor."""
        self.logger = logging.getLogger(__name__)
    
    def extract_documents(self, filing_dir: str) -> Dict[str, str]:
        """Extract documents from a filing.
        
        Args:
            filing_dir: Path to the filing directory.
            
        Returns:
            Dictionary mapping document types to file paths.
        """
        # Check if submission file exists
        submission_path = os.path.join(filing_dir, "submission.txt")
        if not os.path.exists(submission_path):
            self.logger.error(f"Submission file not found in {filing_dir}")
            return {}
        
        try:
            # Read the submission file
            with open(submission_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            
            # Split the content into documents
            documents = self._split_submission(content)
            
            # Save each document to a file
            document_paths = {}
            for doc_type, doc_content in documents.items():
                # Use appropriate extensions
                if doc_type == "xbrl":
                    ext = ".xml"
                elif doc_type == "html":
                    ext = ".html"
                else:
                    ext = ".txt"
                
                file_path = os.path.join(filing_dir, f"{doc_type}{ext}")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(doc_content)
                document_paths[doc_type] = file_path
            
            return document_paths
            
        except Exception as e:
            self.logger.error(f"Error extracting documents from {filing_dir}: {str(e)}")
            return {}
    
    def _split_submission(self, content: str) -> Dict[str, str]:
        """Split a submission file into individual documents.
        
        Args:
            content: Content of the submission file.
            
        Returns:
            Dictionary mapping document types to content.
        """
        # This is a simplified implementation
        # In a real-world scenario, we would parse the SGML/XML structure
        
        documents = {
            "submission": content
        }
        
        # Look for XBRL content
        if "<XBRL>" in content and "</XBRL>" in content:
            xbrl_start = content.find("<XBRL>")
            xbrl_end = content.find("</XBRL>") + len("</XBRL>")
            documents["xbrl"] = content[xbrl_start:xbrl_end]
        
        # Look for XML content
        if "<?xml" in content and "<XML>" in content and "</XML>" in content:
            xml_start = content.find("<XML>")
            xml_end = content.find("</XML>") + len("</XML>")
            documents["xml"] = content[xml_start:xml_end]
        
        # Look for HTML content
        if "<HTML>" in content and "</HTML>" in content:
            html_start = content.find("<HTML>")
            html_end = content.find("</HTML>") + len("</HTML>")
            documents["html"] = content[html_start:html_end]
        
        return documents
    
    def extract_income_statement(self, filing_dir: str) -> Optional[str]:
        """Extract the income statement from a filing.
        
        Args:
            filing_dir: Path to the filing directory.
            
        Returns:
            Path to the extracted income statement file, or None if not found.
        """
        # Extract all documents
        documents = self.extract_documents(filing_dir)
        
        # Check for XBRL document first
        if "xbrl" in documents:
            xbrl_path = documents["xbrl"]
            # Simple heuristic to check if this contains income statement data
            with open(xbrl_path, "r", encoding="utf-8", errors="replace") as f:
                xbrl_content = f.read(5000) # Read first 5k chars
            
            income_stmt_indicators = [
                "Revenues", "Revenue", "SalesRevenueNet",
                "CostOfRevenue", "GrossProfit",
                "OperatingIncomeLoss", "NetIncomeLoss"
            ]
            
            has_income_stmt = any(indicator in xbrl_content for indicator in income_stmt_indicators)
            
            if has_income_stmt:
                self.logger.info(f"Found potential income statement in XBRL: {xbrl_path}")
                return xbrl_path
        
        # If no XBRL or no income statement in XBRL, check HTML
        if "html" in documents:
            html_path = documents["html"]
            # Simple heuristic to check if this contains income statement data
            with open(html_path, "r", encoding="utf-8", errors="replace") as f:
                html_content = f.read(10000) # Read first 10k chars
            
            income_stmt_indicators = [
                "Consolidated Statements of Income",
                "Consolidated Statements of Operations",
                "Income Statements",
                "Statement of Earnings",
                "Statement of Operations"
            ]
            
            has_income_stmt = any(indicator in html_content for indicator in income_stmt_indicators)
            
            if has_income_stmt:
                self.logger.info(f"Found potential income statement in HTML: {html_path}")
                return html_path
        
        self.logger.warning(f"Could not find income statement in {filing_dir}")
        return None
