from tube_dl.comments import Comments
comment = Comments('https://www.youtube.com/watch?v=-TKjvSsYEd4').process_comments()
print(len(comment))


