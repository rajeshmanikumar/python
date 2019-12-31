import bs4
import pandas as pd
import requests
import re
import psycopg2

def get_span_text (strdata):
    textvaldata = bs4.BeautifulSoup(str(strdata), "html.parser")
    return textvaldata.span.string

def get_ahref_text (strdata):
    textvaldata = bs4.BeautifulSoup(str(strdata), "html.parser")
    return textvaldata.a.string

def get_div_text (strdata):
    textvaldata = bs4.BeautifulSoup(str(strdata), "html.parser")
    return textvaldata.div.string

def get_p_text (strdata):
    textvaldata = bs4.BeautifulSoup(str(strdata), "html.parser")
    return textvaldata.p.string

def get_null_class (soup_data,tag_name):
    textvaldata = soup_data.find_all('p') #class_=None #tag_name'',{'class' : None}
    return textvaldata

def extract_method (soup_data, tag_name, class_name, pos_val):
    #print(class_name)
    #print(class_name.find(","))
    if class_name.find(",") >= 0 :
        getval = soup_data.find_all(tag_name, {'class' : ['metascore favorable','metascore mixed']}) #metascore favorable","metascore  mixed
        #print(class_name)
    else:
        getval = soup_data.find_all(tag_name, {'class' : class_name})
    #print(getval)
    if tag_name == 'span':
        getval_text = get_span_text(getval[pos_val])
    elif tag_name == 'a':
        getval_text = get_ahref_text(getval[pos_val])
    else:
        getval_text = getval #"No Data / Error"
    return getval_text

# Main Method Starts Here
def main():
    # URL of IMDB
    url = 'https://www.imdb.com/search/title/?count=100&groups=top_1000&sort=user_rating'
    def get_page_contents(url):
        page = requests.get(url, headers={"Accept-Language": "en-US"})
        return bs4.BeautifulSoup(page.text, "html.parser")
    # Main URL Parsing
    soup = get_page_contents(url)
    # Get Movie List
    allmovies = soup.findAll('div', class_='lister-item mode-advanced')
    #movie_data = []
    all_movies_data = []
    for movieinfo in allmovies:
        movie_data = []
        #print(movieinfo)
        movie = movieinfo.findAll('h3', class_='lister-item-header')
        #print(str(movie[0]))
        moviesoup = bs4.BeautifulSoup(str(movie[0]), "html.parser")
        
        # Movie Title
        title = get_ahref_text(str(movie[0]))
        print(title)

        # Movie Year
        yearspan = extract_method(moviesoup,'span','lister-item-year text-muted unbold', 0)
        year_info = yearspan.replace("(","").replace(")","")
        print(year_info)

        text_muted_data = extract_method(movieinfo,'p','text-muted', 0)
        #print(text_muted_data)
        
        # Certificate Info
        try:
            certificate_val = extract_method(text_muted_data[0],'span','certificate', 0)
        except:
            certificate_val = 'Not Rated'
        print(certificate_val)

        # Movie Run Time in Minutes
        run_time_mins = extract_method(text_muted_data[0],'span','runtime', 0)
        print(run_time_mins)

        # Movie Genre
        genre_info = extract_method(text_muted_data[0],'span','genre', 0)
        genre_info = genre_info.strip()
        print(genre_info)

        rating_data = extract_method(movieinfo,'div','ratings-bar', 0)
        #print(rating_data)

        # IMDB Rating
        imdb_rate = extract_method(rating_data[0],'span','value', 0)
        print(imdb_rate)

        # MetaScore Rating
        try:
            metascore_rate = extract_method(rating_data[0],'span','["metascore favorable","metascore  mixed"]', 0) #favorable
        except:
            metascore_rate = 'Not Rated'
        print(metascore_rate)

        #print(text_muted_data[1])
        # Story Plot
        story_plot = get_p_text(text_muted_data[1]) #extract_method(text_muted_data[1],'p','text-muted', 0)
        #story_plot = story_plot.strip()
        print(story_plot)

        more_mov_info = movieinfo.findAll('div', class_='lister-item-content') #get_null_class(moviesoup)
        temp_data = get_null_class(more_mov_info[0],'a')
        #print(temp_data[2]) 

        # Movie Crew Info
        crew_info = temp_data[2].findAll('a') #get_null_class(tcrew_info[0],'a')
        #print(crew_info)
        crew_list_urls = str(crew_info).split(",")
        crew_list = []
        for crew_mate in crew_list_urls:
            #print(crew_mate)
            #print(get_ahref_text(crew_mate))
            crew_list.append(get_ahref_text(crew_mate))
        
        director_name = crew_list[0]
        print(director_name)
        print(crew_list)
        
        vote_gross_info_urls = temp_data[3].findAll('span')
        # Movie Votes
        vote_info = get_span_text(vote_gross_info_urls[1])
        print(vote_info)
        # Movie Gross
        try:
            gross_info = get_span_text(vote_gross_info_urls[4])
            gross_info = gross_info[1:-1]
        except:
            gross_info = 0
        print(gross_info)

        movie_data.append(title)
        movie_data.append(year_info)
        movie_data.append(certificate_val)
        movie_data.append(run_time_mins)
        movie_data.append(genre_info)
        movie_data.append(imdb_rate)
        movie_data.append(metascore_rate)
        movie_data.append(story_plot)
        movie_data.append(director_name)
        movie_data.append(crew_list)
        movie_data.append(vote_info)
        movie_data.append(gross_info)
        #print(movie_data)
        all_movies_data.append(movie_data)
        #print(all_movies_data)

        #break
    # List to Data Frame
    df = pd.DataFrame(all_movies_data, columns = ['Movie_Title', 'Movie_Year','Movie_Certificate',
        'Movie_RunTime_Mins','Movie_Genre','Movie_IMDB_Rate','Movie_MetaScore','Movie_Story_Plot',
        'Movie_Director','Movie_Crew','Movie_Votes','Movie_Gross_M$'])
    print(df.head())

    # DB Insert
    try:
        connection = psycopg2.connect(user="postgres",
                                    password="pg2050",
                                    host="127.0.0.1",
                                    port="5432",
                                    database="TestDB")
        cursor = connection.cursor()
        for rows in all_movies_data:
            postgres_insert_query = """ INSERT INTO imdb_data (title,movie_year,certificate_info,
                run_time_mins,genre_info,imdb_rate,metascore_rate,story_plot,
                movie_director,movie_crew,vote_info,gross_info) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            cursor.execute(postgres_insert_query, rows)

        connection.commit()
    except (Exception, psycopg2.Error) as error :
        print ("Error while fetching data from PostgreSQL", error)

    finally:
        #closing database connection.
        if(connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")
    

    print ("Ends Here")

if __name__== "__main__":
  main()