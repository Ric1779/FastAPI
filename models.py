from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# Notes: back_populates in database models
#
# back_populates is purely an in-memory convenience, it has nothing to do with the database. 
# The database only cares about user_id (the foreign key). back_populates just tells SQLAlchemy 
# "when you update one side, please update the other side too, right now, in Python, without 
# waiting for a DB round-trip".

# class User(Base):
#     posts: Mapped[list[Post]] = relationship(back_populates="author")
#     #             ^^^^^^^^^^
#     #             "this side is a list, so I manage a collection"

# class Post(Base):
#     author: Mapped[User] = relationship(back_populates="posts")
#     #              ^^^^
#     #             Step 1: "the other model is User"
#     #                                                 ^^^^^
#     #                                                 Step 2: "the attribute to sync is called 'posts'"
# When you do post.author = alice, SQLAlchemy thinks:

# "The mirror of author is called posts" - from back_populates="posts"
# "Let me go look at User.posts"
# "It's Mapped[list[Post]] — a collection, so I should append, not overwrite"
# Appends post to alice.posts

# If it were Mapped[Post] (no list), it would assign instead of append. So yes, 
# the list in the type hint is exactly what drives that decision.

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    image_file: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        default=None,
    )

    posts: Mapped[list[Post]] = relationship(back_populates="author", cascade="all, delete-orphan")

    @property
    def image_path(self) -> str:
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    date_posted: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    author: Mapped[User] = relationship(back_populates="posts")