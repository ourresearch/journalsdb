from app import app, db
from models.journal import Journal
from models.price import SubscriptionPriceNew


@app.cli.command("subscription_conversion")
def subscription_conversion():
    journals = Journal.query.all()

    for j in journals:
        if j.subscription_prices:
            for s in j.subscription_prices:
                new_price = SubscriptionPriceNew(
                    journal_id=j.id,
                    price=s.price,
                    country=s.country,
                    currency=s.currency,
                    region=s.region,
                    fte_from=s.fte_from,
                    fte_to=s.fte_to,
                    year=s.year,
                )
                db.session.add(new_price)
                print("adding new price {} for id {}".format(s.price, j.id))
    db.session.commit()
