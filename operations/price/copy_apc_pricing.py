from app import app, db
from models.journal import Journal
from models.price import APCPriceNew


@app.cli.command("copy_apc_pricing")
def copy_apc_pricing():
    journals = Journal.query.all()
    for journal in journals:
        if journal.apc_prices:
            for price in journal.apc_prices:
                new_apc_price = APCPriceNew(
                    journal_id=journal.id,
                    price=price.price,
                    currency_id=price.currency_id,
                    country_id=price.country_id,
                    region_id=price.region_id,
                    year=price.year,
                )
                db.session.add(new_apc_price)
        print(f"prices added for journal with id {journal.id}")
    db.session.commit()
