from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, desc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
import os

AUTH = os.environ["AUTH"]
ENDPOINT = "https://api.themoviedb.org/3/search/movie"
HEADERS = {
    "accept": "application/json",
    "Authorization": AUTH
}

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///my_movies.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Edit form
class UpdateForm(FlaskForm):
    rating = FloatField('Your Rating Out of 10', validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField("Done")


class AddMovie(FlaskForm):
    name = StringField("Movie Name", validators=[DataRequired()])
    search = SubmitField("Search")


# CREATE TABLE
class Movies(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=True)


with app.app_context():
    db.create_all()


# Manual adding record
# with app.app_context():
#     new_movie = Movies(
#         title="Avatar The Way of Water",
#         year=2022,
#         description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#         rating=7.3,
#         ranking=9,
#         review="I liked the water.",
#         img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
#     )
#     db.session.add(new_movie)
#     db.session.commit()

@app.route("/")
def home():
    with app.app_context():
        result = db.session.execute(db.select(Movies).order_by(desc(Movies.rating)))
        all_movies = result.scalars().all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = i+1
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    form = UpdateForm()
    movie_id = request.args.get("id")
    if form.validate_on_submit():
        with app.app_context():
            movie_to_update = db.session.execute(db.select(Movies).where(Movies.id == movie_id)).scalar()
            movie_to_update.rating = form.rating.data
            movie_to_update.review = form.review.data
            db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    with app.app_context():
        movie_to_delete = db.session.execute(db.select(Movies).where(Movies.id == movie_id)).scalar()
        # or movie_to_delete = db.get_or_404(Book, book_id)
        db.session.delete(movie_to_delete)
        db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=['GET', 'POST'])
def add_movie():
    form = AddMovie()
    if form.validate_on_submit():
        movie = form.name.data
        return redirect(url_for('select', search_movie=movie))
    return render_template('add.html', form=form)


@app.route("/select")
def select():
    search_movie = request.args.get("search_movie")
    params = {
        "query": search_movie
    }
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    data = response.json()['results']
    return render_template('select.html', data=data)


@app.route("/find")
def find():
    tmdb_id = request.args.get("tmdb_id")
    tmdb_endpoint = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    response = requests.get(url=tmdb_endpoint, headers=HEADERS)
    data = response.json()
    new_movie = Movies(
        title=data["title"],
        img_url=f"https://image.tmdb.org/t/p/w500{data["poster_path"]}",
        year=data["release_date"].split("-")[0],
        description=data["overview"]
    )
    with app.app_context():
        db.session.add(new_movie)
        db.session.commit()
        current_movie = db.session.execute(db.select(Movies).where(Movies.title == data["title"])).scalar()
    return redirect(url_for('edit', id=current_movie.id))


if __name__ == '__main__':
    app.run(debug=True)

'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''
