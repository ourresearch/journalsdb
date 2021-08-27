from app import app, db
from models.price import MiniBundle, MiniBundlePrice


@app.cli.command("mini_bundle_conversion")
def mini_bundle_conversion():
    mini_bundles = MiniBundle.query.all()

    for m in mini_bundles:
        for s in m.subscription_prices:
            new_mb_price = MiniBundlePrice(
                mini_bundle_id=m.id,
                price=s.price,
                country=s.country,
                currency=s.currency,
                region=s.region,
                year=s.year,
            )
            db.session.add(new_mb_price)
            print("adding new price {} for id {}".format(s.price, m.id))
    db.session.commit()
