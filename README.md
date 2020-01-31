# Customer Searching

This tool helps you to analyze your subscribers activity on social networks:  
     - [instagram](https://www.instagram.com/)  
     - [facebook](https://www.facebook.com/)  
     - [vk](https://vk.com/)  

You will know, who comments and likes your posts most of all.

## Prerequisites

Python3 should be already installed.

## How to install and configure

- ```bash
  $ git clone https://github.com/nicko858/customer-searching.git
  $ cd customer-searching
  $ pip install -r requirements.txt
  ```

- Create `.env` file in the root of `customer-searching`
- Follow the instructions `VK instructions`, `Facebook instructions` from [this](https://github.com/nicko858/smm-reposting) repo.  
**(!!You'll also need `groups_access_member_info` - permissions for `graph.facebook`)**
- Also, add the following records to your `.env` -file:

    ```bash
    INSTA_LOGIN=<instagram login>
    INSTA_PASSWORD=<instagram password>
    INSTA_VENDOR=<instagram vendor name>

    VK_VENDOR=<vk vendor name>
    FACEBOOK_GROUP=<your facebook group id>
    ```

## How to run

Script is launched with the required parameter - `social_network`.  
It may be in:  [`vk`, `instagram`, `facebook`]  

Example:

```bash
    $ cd customer-searching
    $ smm_analyze.py instagram
```

## Project Goals

The code is written for educational purposes on online-course for web-developers [dvmn.org](https://dvmn.org/).
