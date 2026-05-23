from __future__ import annotations

from typing import Any


TOOL_CONFIGS: dict[str, dict[str, Any]] = {
    "mortgage-payment-calculator": {
        "name": "Mortgage Payment Calculator",
        "description": "Estimate a monthly mortgage payment using price, down payment, rate, term, and escrow.",
        "category": "finance",
        "formula": "mortgage",
        "inputs": [
            ["price", "Home price", "Purchase price", "300000"],
            ["down", "Down payment", "Cash down", "60000"],
            ["rate", "Interest rate %", "Annual rate", "6.75"],
            ["years", "Loan term years", "Common terms are 15 or 30", "30"],
            ["escrow", "Monthly taxes and insurance", "Optional monthly estimate", "350"],
        ],
        "faq": [
            ["Is this a lender quote?", "No. It is an educational estimate, not a lender quote or financial advice."],
            ["Does this include taxes and insurance?", "Only if you enter a monthly estimate for taxes and insurance."],
        ],
    },
    "paycheck-estimator": {
        "name": "Paycheck Take-Home Estimator",
        "description": "Estimate take-home pay after tax percentages and deductions.",
        "category": "work",
        "formula": "paycheck",
        "inputs": [
            ["gross", "Gross pay per check", "Before taxes and deductions", "2200"],
            ["federal", "Federal tax %", "Estimate only", "12"],
            ["state", "State and local tax %", "Estimate only", "5"],
            ["deduct", "Other deductions", "Insurance, retirement, and other deductions", "150"],
        ],
        "faq": [
            ["Is this a payroll calculator?", "No. It is a simple estimate and is not tax, payroll, or financial advice."],
            ["Why might my real check differ?", "Payroll rules, benefits, pretax deductions, and local taxes can change the actual amount."],
        ],
    },
    "time-card-calculator": {
        "name": "Time Card Calculator",
        "description": "Estimate regular pay, overtime pay, and total gross pay from hours worked.",
        "category": "work",
        "formula": "timecard",
        "inputs": [
            ["rate", "Hourly rate", "Your regular hourly pay", "18"],
            ["regular", "Regular hours", "Hours paid at normal rate", "40"],
            ["overtime", "Overtime hours", "Hours paid at overtime rate", "5"],
            ["multiplier", "Overtime multiplier", "Common overtime multiplier is 1.5", "1.5"],
        ],
        "faq": [
            ["Does this include taxes?", "No. It estimates gross pay before taxes and deductions."],
            ["Is overtime always 1.5x?", "Not always. Use the multiplier that applies to your situation."],
        ],
    },
    "car-payment-calculator": {
        "name": "Car Payment Calculator",
        "description": "Estimate a monthly car payment from price, down payment, rate, and loan term.",
        "category": "finance",
        "formula": "car",
        "inputs": [
            ["price", "Vehicle price", "Purchase price", "28000"],
            ["down", "Down payment", "Cash down or trade-in", "3000"],
            ["rate", "APR %", "Annual percentage rate", "7.25"],
            ["months", "Loan term months", "Common terms are 48, 60, or 72", "60"],
        ],
        "faq": [
            ["Does this include taxes and fees?", "No. Add taxes and fees into the vehicle price if you want them included."],
            ["Is this financial advice?", "No. It is an educational estimate only."],
        ],
    },
    "loan-early-payoff-calculator": {
        "name": "Loan Early Payoff Calculator",
        "description": "Estimate how extra monthly payments may reduce payoff time and interest.",
        "category": "finance",
        "formula": "earlyloan",
        "inputs": [
            ["balance", "Current balance", "Amount still owed", "12000"],
            ["rate", "APR %", "Annual interest rate", "9.5"],
            ["payment", "Regular monthly payment", "300"],
            ["extra", "Extra monthly payment", "Additional amount", "75"],
        ],
        "faq": [
            ["What does interest saved mean?", "It compares regular payments with regular plus extra payments."],
            ["Will my lender match this exactly?", "No. Lender terms, fees, and payment timing can change results."],
        ],
    },
    "tip-calculator": {
        "name": "Tip Calculator",
        "description": "Calculate tip amount, total bill, and split amount quickly.",
        "category": "everyday",
        "formula": "tip",
        "inputs": [
            ["bill", "Bill amount", "Before tip", "64.50"],
            ["tip", "Tip percent", "Common choices are 15, 18, 20, or 25", "20"],
            ["people", "Number of people", "Split the total", "2"],
        ],
        "faq": [
            ["Can I split the bill?", "Yes. Enter the number of people and the total will be divided evenly."],
            ["Does this include tax?", "Enter whatever bill amount you want to tip on."],
        ],
    },
    "hourly-to-salary-calculator": {
        "name": "Hourly To Salary Calculator",
        "description": "Convert hourly pay into weekly, monthly, and yearly gross pay estimates.",
        "category": "work",
        "formula": "hourlysalary",
        "inputs": [
            ["rate", "Hourly rate", "Your hourly pay", "22"],
            ["hours", "Hours per week", "Expected weekly hours", "40"],
            ["weeks", "Weeks per year", "Use 52 for full-year work", "52"],
        ],
        "faq": [
            ["Is this before taxes?", "Yes. This estimates gross pay before taxes and deductions."],
            ["Does it include overtime?", "No. Use a time card calculator for overtime scenarios."],
        ],
    },
    "savings-goal-calculator": {
        "name": "Savings Goal Calculator",
        "description": "Estimate how long it may take to reach a savings goal.",
        "category": "finance",
        "formula": "savingsgoal",
        "inputs": [
            ["goal", "Savings goal", "Target amount", "5000"],
            ["current", "Current savings", "Amount saved already", "800"],
            ["monthly", "Monthly savings", "Amount added each month", "250"],
        ],
        "faq": [
            ["Does this include investment growth?", "No. This simple version does not assume interest or investment returns."],
            ["What if I save irregularly?", "Use your average monthly savings amount."],
        ],
    },
    "unit-price-calculator": {
        "name": "Unit Price Calculator",
        "description": "Compare item prices by cost per unit.",
        "category": "shopping",
        "formula": "unitprice",
        "inputs": [
            ["price", "Package price", "Total price", "12.99"],
            ["units", "Package units", "Ounces, count, pounds, or other units", "24"],
            ["compare", "Comparison package price", "Optional second price", "9.99"],
            ["compareunits", "Comparison package units", "Optional second unit count", "16"],
        ],
        "faq": [
            ["What unit should I use?", "Use the same unit for both items, such as ounces, pounds, or count."],
            ["Why is unit price useful?", "It helps compare different package sizes more fairly."],
        ],
    },
    "discount-calculator": {
        "name": "Discount Calculator",
        "description": "Calculate sale price and savings from a percent discount.",
        "category": "shopping",
        "formula": "discount",
        "inputs": [
            ["price", "Original price", "Before discount", "80"],
            ["discount", "Discount %", "Percent off", "25"],
        ],
        "faq": [
            ["Does this include tax?", "No. This calculates the discount before sales tax."],
            ["Can I use it for coupons?", "Yes, if the coupon is a simple percent off."],
        ],
    },
    "sales-tax-calculator": {
        "name": "Sales Tax Calculator",
        "description": "Estimate sales tax and total price from a tax rate.",
        "category": "shopping",
        "formula": "salestax",
        "inputs": [
            ["price", "Item price", "Before tax", "100"],
            ["tax", "Sales tax %", "Local tax rate", "7"],
        ],
        "faq": [
            ["Is this exact?", "It is an estimate. Local rules and exemptions can change real totals."],
            ["Can I use decimal tax rates?", "Yes. For example, use 7.25 for 7.25 percent."],
        ],
    },
    "percentage-change-calculator": {
        "name": "Percentage Change Calculator",
        "description": "Calculate the percent increase or decrease between two numbers.",
        "category": "math",
        "formula": "percentchange",
        "inputs": [
            ["old", "Starting value", "Original number", "80"],
            ["new", "Ending value", "New number", "100"],
        ],
        "faq": [
            ["Can this show a decrease?", "Yes. A negative result means the value decreased."],
            ["What if the starting value is zero?", "Percentage change from zero is not defined in this simple calculator."],
        ],
    },
}


# === RENDERER_EXPANSION_PACK_2_CONFIGS START ===
TOOL_CONFIGS.update(
{
    "roi-calculator": {
        "name": "Simple ROI Calculator",
        "description": "Estimate return on investment from cost and return values.",
        "category": "business",
        "formula": "roi",
        "inputs": [
            [
                "cost",
                "Initial cost",
                "What you spent or invested",
                "1000"
            ],
            [
                "return",
                "Return value",
                "What came back from the investment",
                "1250"
            ]
        ],
        "faq": [
            [
                "What does ROI mean?",
                "ROI estimates return on investment by comparing gain against cost."
            ],
            [
                "Is this financial advice?",
                "No. This is an estimate-only planning tool, not financial advice."
            ]
        ]
    },
    "recipe-scale-calculator": {
        "name": "Recipe Scale Calculator",
        "description": "Scale an ingredient amount when changing recipe servings.",
        "category": "food",
        "formula": "recipescale",
        "inputs": [
            [
                "original",
                "Original servings",
                "Servings the recipe currently makes",
                "4"
            ],
            [
                "desired",
                "Desired servings",
                "Servings you want to make",
                "6"
            ],
            [
                "quantity",
                "Original ingredient quantity",
                "Amount listed in the original recipe",
                "2"
            ]
        ],
        "faq": [
            [
                "How does recipe scaling work?",
                "The calculator multiplies the original quantity by desired servings divided by original servings."
            ],
            [
                "Can I use any unit?",
                "Yes. Keep the same unit before and after scaling, such as cups, grams, or tablespoons."
            ]
        ]
    },
    "paint-coverage-calculator": {
        "name": "Paint Coverage Calculator",
        "description": "Estimate paintable wall area and gallons needed for a simple room project.",
        "category": "home",
        "formula": "paintcoverage",
        "inputs": [
            [
                "width",
                "Total wall width",
                "Combined wall width in feet",
                "40"
            ],
            [
                "height",
                "Wall height",
                "Wall height in feet",
                "8"
            ],
            [
                "doors",
                "Doors",
                "Number of standard doors to subtract",
                "2"
            ],
            [
                "windows",
                "Windows",
                "Number of standard windows to subtract",
                "4"
            ],
            [
                "coats",
                "Coats",
                "Number of paint coats",
                "2"
            ],
            [
                "coverage",
                "Coverage per gallon",
                "Square feet covered by one gallon",
                "350"
            ]
        ],
        "faq": [
            [
                "How much area does this subtract for doors and windows?",
                "It estimates 21 square feet per door and 15 square feet per window."
            ],
            [
                "Is this exact?",
                "No. Paint coverage varies by surface, product, color change, and application method."
            ]
        ]
    },
    "flooring-calculator": {
        "name": "Flooring Calculator",
        "description": "Estimate flooring square footage, waste allowance, and box count.",
        "category": "home",
        "formula": "flooring",
        "inputs": [
            [
                "length",
                "Room length",
                "Length in feet",
                "12"
            ],
            [
                "width",
                "Room width",
                "Width in feet",
                "10"
            ],
            [
                "waste",
                "Waste allowance",
                "Extra percentage for cuts and mistakes",
                "10"
            ],
            [
                "box",
                "Coverage per box",
                "Square feet covered by one box",
                "20"
            ]
        ],
        "faq": [
            [
                "Why include waste?",
                "Most flooring projects need extra material for cuts, layout, and mistakes."
            ],
            [
                "Is this exact?",
                "No. Confirm measurements and product coverage before buying materials."
            ]
        ]
    },
    "concrete-calculator": {
        "name": "Concrete Calculator",
        "description": "Estimate concrete volume and bag count for a simple slab.",
        "category": "home",
        "formula": "concrete",
        "inputs": [
            [
                "length",
                "Slab length",
                "Length in feet",
                "10"
            ],
            [
                "width",
                "Slab width",
                "Width in feet",
                "8"
            ],
            [
                "depth",
                "Slab depth",
                "Depth in inches",
                "4"
            ],
            [
                "waste",
                "Waste allowance",
                "Extra percentage for spill, uneven ground, and margin",
                "10"
            ],
            [
                "yield",
                "Bag yield",
                "Cubic feet per bag",
                "0.6"
            ]
        ],
        "faq": [
            [
                "Why is depth in inches?",
                "Concrete slab depth is often planned in inches while length and width are measured in feet."
            ],
            [
                "Is this structural advice?",
                "No. This is an estimate-only material calculator, not engineering or construction advice."
            ]
        ]
    }
}
)
# === RENDERER_EXPANSION_PACK_2_CONFIGS END ===


# === RENDERER_EXPANSION_PACK_3_CONFIGS START ===
TOOL_CONFIGS.update(
{
    "conversion-rate-calculator": {
        "name": "Conversion Rate Calculator",
        "description": "Calculate conversion rate from visitors and completed actions.",
        "category": "business",
        "formula": "conversionrate",
        "inputs": [
            [
                "visitors",
                "Visitors",
                "Total visitors, clicks, leads, or opportunities",
                "1000"
            ],
            [
                "conversions",
                "Conversions",
                "Purchases, signups, leads, or completed actions",
                "50"
            ]
        ],
        "faq": [
            [
                "What is conversion rate?",
                "Conversion rate is the percentage of visitors or opportunities that complete a desired action."
            ],
            [
                "Is this a forecast?",
                "No. This is an estimate-only calculator based on the numbers you enter."
            ]
        ]
    },
    "churn-rate-calculator": {
        "name": "Churn Rate Calculator",
        "description": "Calculate customer churn rate from starting customers and customers lost.",
        "category": "business",
        "formula": "churnrate",
        "inputs": [
            [
                "starting",
                "Customers at start",
                "Customers at the beginning of the period",
                "1000"
            ],
            [
                "lost",
                "Customers lost",
                "Customers lost or cancelled during the period",
                "40"
            ]
        ],
        "faq": [
            [
                "What is churn rate?",
                "Churn rate is the percentage of customers lost during a period compared with the starting customer count."
            ],
            [
                "Is this business advice?",
                "No. This is an estimate-only calculator for quick planning and reporting."
            ]
        ]
    }
}
)
# === RENDERER_EXPANSION_PACK_3_CONFIGS END ===
