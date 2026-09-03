"""
tests/test_parse_class.py

Regression tests for parse_class.py, locked in against real fixture
files after manual validation (see project notes: all 6 class fixtures
checked line-by-line against parser output before this suite was written).

Purpose: if future changes (e.g. adding signature extraction) accidentally
break name lookup, CoC-target parsing, or next()-detection, this suite
catches it immediately instead of surfacing during mentor review.
"""
import os
import pytest
from parse_class import parse_class_xml

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "classes")


def fixture_path(filename):
    return os.path.join(FIXTURES_DIR, filename)


# Each entry: (filename, expected_name, expected_extension_of, expected_methods)
# expected_methods is {method_name: calls_next_bool}
TEST_CASES = [
    (
        "SalesInvoiceDPApplicationSuite_IT_Extension.xml",
        "SalesInvoiceDPApplicationSuite_IT_Extension",
        {"target_kind": "classstr", "target_name": "SalesInvoiceDP"},
        {
            "generateInvoiceLinesRelatedInformation": True,
            "getTradeLoopTrans_IT": False,
            "getCustInvoiceTransQueryRun": True,
            "canInsertIntoSalesInvoiceTmp": True,
            "populateSalesInvoiceHeaderFooterTmp": True,
            "populateIntentLetterFields": False,
            "parmSalesInvoiceHeaderFooterTmp_IT": False,
            "populateSalesInvoiceTmp": True,
            "correctFreeItemId": False,
            "sortingPerPackingSlip": False,
            "populateFreeNotes": False,
            "parmSalesInvoiceTmp_IT": False,
            "insertTaxes": True,
            "invoiceTxt": True,  # assignment-form `next` call: str x = next foo(...)
            "processCustInvoiceTransRecords": True,
            "processLinesPerPackingSlip": False,
            "processInvoiceLine": False,
            "processProformaInvoiceLine": False,
            "processNonPackedQty": False,
            "processLine": False,
        },
    ),
    (
        "GeneralJournalAccountEntry_Extension.xml",
        "GeneralJournalAccountEntry_Extension",
        None,  # non-CoC: no [ExtensionOf] in Declaration
        {
            "deCompteAuxLib_Extension_FR": False,
            "deCompteAuxNum_Extension_FR": False,
            "deEcritureLib_FR": False,
            "getCustVendTable_FR": False,  # contains queryRun.next() -- must NOT be flagged as CoC
            "displayIsReversed": False,
            "displayTaxBranchDimension": False,
            "displayTraceNumber": False,
            "inventProfileType_RU": False,
            "postingProfile_RU": False,
            "queryCustVendTrans_FR": False,
            "queryCustVendTransAmount_FR": False,
            "reverseSettlement": False,
            "createLedgerTransSettlement": False,
            "createReverseSettlementRecord": False,
            "manageLedgerTransSettlementWithoutSettleAmounts": False,
            "getAccountingDate": False,
            "canProceedWithSettlement": False,
            "getFiscalCalendarYearRecId": False,
            "updateLedgerCov": False,
            "calculateCashFlowAmountForAccountEntry": False,
            "findBySubledgerVoucherAccountingDate": False,
            "initAmountsForLedgerTransferOpeningSumTmp": False,
            "canReverse": False,
            "checkGeneralJournalEntryAccountingDate": False,
            "checkLedgerEntryJournalizing": False,
            "deLedgerJournalizeSeqNum": False,
            "deOffsetAccounts": False,
            "deTaxRefId": False,
            "checkReversal": False,
            "isAccrualApplicable": False,
            "canReverseForLedgerSettlement": False,
            "getRelatedOriginalDocuments": False,  # has [SysClassNameAttribute(classStr(...))] -- must not false-trigger CoC target parsing
            "deDateLet_FR": False,
            "deEcritureLet_FR": False,
            "deEcritureLetLatest_FR": False,
        },
    ),
    (
        "RegNumCustTable_Extension.xml",
        "RegNumCustTable_Extension",
        None,
        {
            "getVatNumPrimaryRegistrationNumber": False,
            "getPrimaryRegistrationNumber": False,
            "copyPrimaryRegistrationNumberToVATMap": False,
            "updateTaxExemptNumberFromPrimaryAddress": False,
            "getEnterpriseNumberPrimaryRegistrationNumber": False,
            "isTaxExemptNumberUpdatedFromDeliveryAddress": False,
        },
    ),
    (
        "SalesEditLines_SalesParmTable_ApplicationSuite_Extension.xml",
        "SalesEditLines_SalesParmTable_ApplicationSuite_Extension",
        {
            "target_kind": "formdatasourcestr",
            "form_name": "SalesEditLines",
            "datasource_name": "SalesParmTable",
        },
        {"active": True},
    ),
    (
        "RealControlPrecisionInventTransForm_Extension.xml",
        "RealControlPrecisionInventTransForm_Extension",
        {"target_kind": "formstr", "target_name": "InventTrans"},
        {"run": True, "buttonClicked": False},
    ),
    (
        "RealControlPrecisionInventTransNewForm_Extension.xml",
        "RealControlPrecisionInventTransNewForm_Extension",
        {"target_kind": "formstr", "target_name": "InventTransNew"},
        {"run": True, "buttonClicked": False},
    ),
]


@pytest.mark.parametrize(
    "filename,expected_name,expected_extension_of,expected_methods",
    TEST_CASES,
    ids=[case[0] for case in TEST_CASES],
)
def test_class_name(filename, expected_name, expected_extension_of, expected_methods):
    result = parse_class_xml(fixture_path(filename))
    assert result["name"] == expected_name


@pytest.mark.parametrize(
    "filename,expected_name,expected_extension_of,expected_methods",
    TEST_CASES,
    ids=[case[0] for case in TEST_CASES],
)
def test_extension_of(filename, expected_name, expected_extension_of, expected_methods):
    result = parse_class_xml(fixture_path(filename))
    assert result["extension_of"] == expected_extension_of


@pytest.mark.parametrize(
    "filename,expected_name,expected_extension_of,expected_methods",
    TEST_CASES,
    ids=[case[0] for case in TEST_CASES],
)
def test_method_count(filename, expected_name, expected_extension_of, expected_methods):
    result = parse_class_xml(fixture_path(filename))
    assert len(result["methods"]) == len(expected_methods)


@pytest.mark.parametrize(
    "filename,expected_name,expected_extension_of,expected_methods",
    TEST_CASES,
    ids=[case[0] for case in TEST_CASES],
)
def test_calls_next_per_method(filename, expected_name, expected_extension_of, expected_methods):
    result = parse_class_xml(fixture_path(filename))
    actual = {m["name"]: m["calls_next"] for m in result["methods"]}
    assert actual == expected_methods


@pytest.mark.parametrize(
    "filename,expected_name,expected_extension_of,expected_methods",
    TEST_CASES,
    ids=[case[0] for case in TEST_CASES],
)
def test_is_new_method_matches_inverse_of_calls_next(
    filename, expected_name, expected_extension_of, expected_methods
):
    """
    Locks in current behavior (is_new_method = not calls_next) as a
    regression check -- NOT a claim that this logic is semantically
    correct. None of the 6 real fixtures contain a genuine 'forgot to
    call next()' CoC bug, so this assumption remains unproven against
    that specific real-world case. See project notes.
    """
    result = parse_class_xml(fixture_path(filename))
    for method in result["methods"]:
        assert method["is_new_method"] == (not method["calls_next"])