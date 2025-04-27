# Hong Kong Job Fair and Recruitment Event Information Sources

This document catalogs the major sources of job fair and recruitment event information in Hong Kong, with a focus on sources providing information in Traditional Chinese (ZH-HK). The sources are categorized as primary (must-check daily) and secondary (check weekly) based on their importance and update frequency.

## Primary Sources (Check Daily)

### 1. Hong Kong Labour Department (勞工處)
- **Name**: Hong Kong Labour Department Interactive Employment Service
- **Website URL**: https://www2.jobs.gov.hk/0/tc/information/Epem/Vacancy/
- **Type of organization**: Government
- **Languages available**: Traditional Chinese (ZH-HK) and English
- **Types of events typically listed**: Large-scale job fairs, district-based recruitment events, industry-specific recruitment days
- **Update frequency**: Daily updates for upcoming job fairs
- **Data accessibility**: Public webpage, no login required
- **Special notes**: Users can subscribe to job fair notifications through "My GovHK" account. The system sends reminders about one week before each job fair. Events typically feature 50-60 organizations offering thousands of job vacancies across multiple industries.

### 2. JobsDB Hong Kong
- **Name**: JobsDB Recruitment Day (招聘日)
- **Website URL**: https://hk.jobsdb.com/招聘日-recruitment-day-jobs
- **Type of organization**: Private company (job portal)
- **Languages available**: Traditional Chinese (ZH-HK) and English
- **Types of events typically listed**: Company-specific recruitment days, industry-focused hiring events
- **Update frequency**: Daily updates with new recruitment events
- **Data accessibility**: Public webpage, basic information visible without login
- **Special notes**: One of the most comprehensive sources for private company recruitment events. Features both physical and virtual recruitment days. Companies often post detailed event information including exact positions available.

### 3. Hong Kong Trade Development Council (HKTDC)
- **Name**: HKTDC Education & Careers Expo
- **Website URL**: https://www.hktdc.com/event/hkeducationexpo/tc
- **Type of organization**: Statutory body
- **Languages available**: Traditional Chinese (ZH-HK) and English
- **Types of events typically listed**: Annual large-scale education and career expo, featuring recruitment booths, industry seminars, and on-site interviews
- **Update frequency**: Daily updates during the expo period (typically January), regular updates year-round
- **Data accessibility**: Public webpage, no login required
- **Special notes**: The annual expo features over 800 organizations from 22+ countries/regions, offering 4,000+ job opportunities. Includes specialized zones for different industries and "CV Clinic" services. The 2025 expo is scheduled for January 16-19.

## Secondary Sources (Check Weekly)

### 4. University Career Centers

#### 4.1 The University of Hong Kong (HKU)
- **Name**: HKU CEDARS (Centre of Development and Resources for Students)
- **Website URL**: https://www.cedars.hku.hk/careers
- **Type of organization**: University
- **Languages available**: English primary, some Traditional Chinese (ZH-HK)
- **Types of events typically listed**: Campus recruitment fairs, career talks, industry-specific recruitment events
- **Update frequency**: Weekly updates, more frequent during peak recruitment seasons
- **Data accessibility**: Public webpage, some events may require HKU login
- **Special notes**: Hosts annual job fair in February featuring 170+ companies offering 9,000+ positions. Also organizes "Career Development Month" with 80+ industry sharing sessions and workshops.

#### 4.2 The Chinese University of Hong Kong (CUHK)
- **Name**: CUHK Career Planning and Development Centre
- **Website URL**: https://cpdc.osa.cuhk.edu.hk/
- **Type of organization**: University
- **Languages available**: Traditional Chinese (ZH-HK) and English
- **Types of events typically listed**: Campus recruitment fairs, career talks, industry-specific recruitment events
- **Update frequency**: Weekly updates
- **Data accessibility**: Public webpage, some events may require CUHK login
- **Special notes**: Hosts regular recruitment events throughout the academic year, with major fairs in fall and spring semesters.

#### 4.3 Hong Kong Polytechnic University (PolyU)
- **Name**: PolyU Careers and Placement Section
- **Website URL**: https://www.polyu.edu.hk/caps/
- **Type of organization**: University
- **Languages available**: Traditional Chinese (ZH-HK) and English
- **Types of events typically listed**: Campus recruitment fairs, career talks, industry-specific recruitment events
- **Update frequency**: Weekly updates
- **Data accessibility**: Public webpage, some events may require PolyU login
- **Special notes**: Organizes industry-specific recruitment events throughout the year.

### 5. Hong Kong International Education and Employment Exhibition (HKIEEE)
- **Name**: Hong Kong International Education and Employment Exhibition
- **Website URL**: https://www.hkiee.com.hk/tc/
- **Type of organization**: Private exhibition organizer
- **Languages available**: Traditional Chinese (ZH-HK) and English
- **Types of events typically listed**: Annual education and employment exhibition held in July
- **Update frequency**: Monthly updates, more frequent approaching the exhibition date
- **Data accessibility**: Public webpage, no login required
- **Special notes**: Focuses on both education and employment opportunities, featuring local and overseas universities, vocational training institutions, and employers.

### 6. CPJobs
- **Name**: CPJobs Career Events
- **Website URL**: https://www.cpjobs.com/hk/career-advice/latest-and-upcoming-job-fair-career-events-watch
- **Type of organization**: Private company (job portal by South China Morning Post)
- **Languages available**: English primary, some Traditional Chinese (ZH-HK)
- **Types of events typically listed**: Industry-specific job fairs, career development events
- **Update frequency**: Weekly updates
- **Data accessibility**: Public webpage, no login required
- **Special notes**: Provides information about upcoming job fairs across various industries including finance, technology, education, and real estate.

### 7. JobDailyHK
- **Name**: JobDailyHK Recruitment Day
- **Website URL**: https://www.jobdailyhk.com/job/tag/Recruitment+Day+招聘日
- **Type of organization**: Private company (job portal)
- **Languages available**: Traditional Chinese (ZH-HK) primary
- **Types of events typically listed**: Company recruitment days, industry job fairs
- **Update frequency**: Weekly updates
- **Data accessibility**: Public webpage, no login required
- **Special notes**: Focuses primarily on local Hong Kong companies and recruitment events.

### 8. Moovup
- **Name**: Moovup Good Jobs Express (好工速遞)
- **Website URL**: https://moovup.com/hk/
- **Type of organization**: Private company (job portal)
- **Languages available**: Traditional Chinese (ZH-HK) primary
- **Types of events typically listed**: Company recruitment days, walk-in interviews
- **Update frequency**: Weekly updates
- **Data accessibility**: Public webpage, no login required
- **Special notes**: Specializes in blue-collar and service industry positions, with many physical recruitment events.

## Data Extraction Challenges and Considerations

1. **Language Processing**: Most primary sources provide information in Traditional Chinese (ZH-HK), requiring proper character encoding and language processing capabilities.

2. **Inconsistent Data Formats**: Different platforms present event information in varying formats, making standardized extraction challenging.

3. **Dynamic Content**: Many sites use JavaScript to load content dynamically, requiring browser automation or API access for complete data extraction.

4. **Limited API Access**: Most platforms do not offer public APIs for data access, necessitating web scraping approaches.

5. **Event Details Depth**: While basic event information (date, location, title) is usually readily available, detailed information about participating companies and specific positions may require deeper navigation.

6. **Frequency Considerations**: Primary sources should be checked daily as they update frequently with new events, while secondary sources can be checked weekly.

7. **Calendar Integration**: When extracting data for Google Calendar integration, attention must be paid to proper formatting of date/time information and location details.

8. **Mobile Optimization**: Some sources are primarily designed for mobile access, which may affect scraping approaches.

9. **Authentication Requirements**: Some university career centers require student/alumni login for full access to event details.

10. **Seasonal Variations**: Job fair frequency varies throughout the year, with peak periods typically in January-February and September-October.
