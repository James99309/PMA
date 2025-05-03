/**
 * 国家和地区选择器静态数据
 * 用于客户管理模块
 */
const countryData = [
  { code: "CN", name: "中国" },
  { code: "US", name: "美国" },
  { code: "JP", name: "日本" },
  { code: "DE", name: "德国" },
  { code: "FR", name: "法国" },
  { code: "GB", name: "英国" },
  { code: "CA", name: "加拿大" },
  { code: "AU", name: "澳大利亚" },
  { code: "NZ", name: "新西兰" },
  { code: "IN", name: "印度" },
  { code: "RU", name: "俄罗斯" },
  { code: "BR", name: "巴西" },
  { code: "ZA", name: "南非" },
  { code: "SG", name: "新加坡" },
  { code: "MY", name: "马来西亚" },
  { code: "TH", name: "泰国" },
  { code: "ID", name: "印度尼西亚" },
  { code: "PH", name: "菲律宾" },
  { code: "VN", name: "越南" },
  { code: "KR", name: "韩国" },
  { code: "AE", name: "阿联酋" },
  { code: "SA", name: "沙特阿拉伯" },
  { code: "IT", name: "意大利" },
  { code: "ES", name: "西班牙" },
  { code: "NL", name: "荷兰" },
  { code: "CH", name: "瑞士" },
  { code: "SE", name: "瑞典" },
  { code: "NO", name: "挪威" },
  { code: "FI", name: "芬兰" },
  { code: "DK", name: "丹麦" },
  { code: "BE", name: "比利时" }
];

const regionData = {
  "CN": [
    "北京市", "上海市", "天津市", "重庆市", 
    "河北省", "山西省", "辽宁省", "吉林省", "黑龙江省", 
    "江苏省", "浙江省", "安徽省", "福建省", "江西省", "山东省", 
    "河南省", "湖北省", "湖南省", "广东省", "海南省", "四川省", 
    "贵州省", "云南省", "陕西省", "甘肃省", "青海省", "台湾省",
    "内蒙古自治区", "广西壮族自治区", "西藏自治区", "宁夏回族自治区", "新疆维吾尔自治区",
    "香港特别行政区", "澳门特别行政区"
  ],
  "US": [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", 
    "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", 
    "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", 
    "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", 
    "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", 
    "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", 
    "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", 
    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming",
    "District of Columbia"
  ],
  "JP": [
    "東京都", "大阪府", "北海道", "愛知県", "神奈川県", "福岡県", "兵庫県", "京都府", 
    "千葉県", "埼玉県", "静岡県", "広島県", "宮城県", "新潟県", "岡山県", "熊本県",
    "鹿児島県", "沖縄県", "群馬県", "栃木県", "茨城県", "岐阜県", "長野県", "山形県",
    "福島県", "三重県", "愛媛県", "香川県", "青森県", "秋田県", "山梨県", "石川県",
    "和歌山県", "滋賀県", "奈良県", "大分県", "宮崎県", "佐賀県", "長崎県", "徳島県",
    "高知県", "富山県", "福井県", "島根県", "鳥取県", "岩手県"
  ],
  "DE": [
    "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", "Hamburg", "Hessen",
    "Mecklenburg-Vorpommern", "Niedersachsen", "Nordrhein-Westfalen", "Rheinland-Pfalz",
    "Saarland", "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"
  ],
  "FR": [
    "Île-de-France", "Auvergne-Rhône-Alpes", "Hauts-de-France", "Nouvelle-Aquitaine",
    "Occitanie", "Grand Est", "Provence-Alpes-Côte d'Azur", "Normandie", "Bretagne",
    "Pays de la Loire", "Bourgogne-Franche-Comté", "Centre-Val de Loire", "Corse"
  ],
  "GB": [
    "England", "Scotland", "Wales", "Northern Ireland", 
    "London", "Manchester", "Birmingham", "Glasgow", "Liverpool", "Edinburgh", 
    "Bristol", "Sheffield", "Leeds", "Newcastle", "Nottingham", "Cardiff", "Belfast"
  ],
  "CA": [
    "Ontario", "Quebec", "British Columbia", "Alberta", "Manitoba", "Saskatchewan",
    "Nova Scotia", "New Brunswick", "Newfoundland and Labrador", "Prince Edward Island",
    "Northwest Territories", "Yukon", "Nunavut"
  ],
  "AU": [
    "New South Wales", "Victoria", "Queensland", "Western Australia", 
    "South Australia", "Tasmania", "Australian Capital Territory", "Northern Territory"
  ],
  "NZ": [
    "Auckland", "Wellington", "Canterbury", "Waikato", "Bay of Plenty", "Otago",
    "Manawatu-Wanganui", "Hawke's Bay", "Northland", "Taranaki", "Southland",
    "Gisborne", "Marlborough", "West Coast", "Tasman", "Nelson"
  ],
  "IN": [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
    "Uttarakhand", "West Bengal", "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry"
  ],
  "RU": [
    "Moscow", "Saint Petersburg", "Novosibirsk", "Yekaterinburg", "Nizhny Novgorod",
    "Kazan", "Chelyabinsk", "Omsk", "Samara", "Rostov-on-Don", "Ufa", "Krasnoyarsk",
    "Perm", "Voronezh", "Volgograd", "Krasnodar", "Saratov", "Tyumen", "Izhevsk",
    "Barnaul", "Irkutsk", "Khabarovsk", "Vladivostok"
  ],
  "BR": [
    "São Paulo", "Rio de Janeiro", "Minas Gerais", "Bahia", "Rio Grande do Sul",
    "Paraná", "Pernambuco", "Ceará", "Pará", "Goiás", "Amazonas", "Espírito Santo",
    "Maranhão", "Mato Grosso", "Paraíba", "Santa Catarina", "Mato Grosso do Sul",
    "Piauí", "Alagoas", "Rio Grande do Norte", "Sergipe", "Tocantins", "Acre",
    "Amapá", "Roraima", "Distrito Federal"
  ],
  "ZA": [
    "Gauteng", "KwaZulu-Natal", "Western Cape", "Eastern Cape", "North West", 
    "Free State", "Mpumalanga", "Limpopo", "Northern Cape"
  ],
  "SG": ["Singapore"],
  "MY": [
    "Selangor", "Kuala Lumpur", "Johor", "Penang", "Sarawak", "Sabah", "Perak",
    "Negeri Sembilan", "Pahang", "Melaka", "Kedah", "Terengganu", "Kelantan",
    "Perlis", "Labuan", "Putrajaya"
  ],
  "TH": [
    "Bangkok", "Chiang Mai", "Phuket", "Pattaya", "Krabi", "Koh Samui", "Hua Hin",
    "Ayutthaya", "Chiang Rai", "Kanchanaburi", "Khon Kaen", "Nakhon Ratchasima",
    "Hat Yai", "Udon Thani"
  ],
  "ID": [
    "Jakarta", "West Java", "East Java", "Central Java", "North Sumatra", "Banten",
    "South Sulawesi", "Bali", "Yogyakarta", "Riau", "South Sumatra", "Lampung",
    "West Sumatra", "Papua", "Aceh", "West Nusa Tenggara", "East Kalimantan",
    "East Nusa Tenggara"
  ],
  "PH": [
    "Metro Manila", "Cebu", "Davao", "Calabarzon", "Central Luzon", "Central Visayas",
    "Western Visayas", "Soccsksargen", "Northern Mindanao", "Bicol Region"
  ],
  "VN": [
    "Ho Chi Minh City", "Hanoi", "Da Nang", "Hai Phong", "Can Tho", "Bien Hoa",
    "Hue", "Nha Trang", "Buon Ma Thuot", "Vinh", "Nam Dinh", "Qui Nhon", "Vung Tau"
  ],
  "KR": [
    "Seoul", "Busan", "Incheon", "Daegu", "Daejeon", "Gwangju", "Ulsan", "Sejong",
    "Gyeonggi-do", "Gangwon-do", "Chungcheongbuk-do", "Chungcheongnam-do",
    "Jeollabuk-do", "Jeollanam-do", "Gyeongsangbuk-do", "Gyeongsangnam-do", "Jeju-do"
  ],
  "AE": [
    "Abu Dhabi", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"
  ],
  "SA": [
    "Riyadh", "Makkah", "Madinah", "Eastern Province", "Asir", "Tabuk", "Hail", "Jizan",
    "Najran", "Al Bahah", "Al Jawf", "Northern Borders"
  ],
  "IT": [
    "Lombardy", "Lazio", "Campania", "Sicily", "Veneto", "Piedmont", "Emilia-Romagna",
    "Tuscany", "Apulia", "Calabria", "Sardinia", "Liguria", "Marche", "Abruzzo",
    "Friuli Venezia Giulia", "Trentino-Alto Adige", "Umbria", "Basilicata", "Molise",
    "Valle d'Aosta"
  ],
  "ES": [
    "Madrid", "Catalonia", "Andalusia", "Valencia", "Galicia", "Castile and León",
    "Basque Country", "Castilla-La Mancha", "Canary Islands", "Aragon", "Murcia",
    "Balearic Islands", "Extremadura", "Asturias", "Navarre", "Cantabria", "La Rioja",
    "Ceuta", "Melilla"
  ],
  "NL": [
    "North Holland", "South Holland", "North Brabant", "Gelderland", "Utrecht", "Limburg",
    "Overijssel", "Flevoland", "Groningen", "Friesland", "Drenthe", "Zeeland"
  ],
  "CH": [
    "Zürich", "Bern", "Vaud", "Aargau", "St. Gallen", "Geneva", "Lucerne", "Ticino",
    "Valais", "Basel-Stadt", "Basel-Landschaft", "Thurgau", "Fribourg", "Solothurn",
    "Neuchâtel", "Graubünden", "Schwyz", "Zug", "Schaffhausen", "Jura", "Appenzell Ausserrhoden",
    "Nidwalden", "Glarus", "Obwalden", "Uri", "Appenzell Innerrhoden"
  ],
  "SE": [
    "Stockholm", "Västra Götaland", "Skåne", "Östergötland", "Uppsala", "Jönköping",
    "Halland", "Örebro", "Södermanland", "Dalarna", "Gävleborg", "Västerbotten",
    "Värmland", "Västmanland", "Norrbotten", "Västernorrland", "Kalmar", "Kronoberg",
    "Blekinge", "Jämtland", "Gotland"
  ],
  "NO": [
    "Oslo", "Viken", "Vestland", "Rogaland", "Trøndelag", "Vestfold og Telemark",
    "Agder", "Innlandet", "Møre og Romsdal", "Nordland", "Troms og Finnmark"
  ],
  "FI": [
    "Uusimaa", "Pirkanmaa", "Southwest Finland", "North Ostrobothnia", "Central Finland",
    "North Savo", "Satakunta", "Päijät-Häme", "South Savo", "Kymenlaakso", "Lapland",
    "South Ostrobothnia", "Kanta-Häme", "North Karelia", "Central Ostrobothnia",
    "Ostrobothnia", "Kainuu", "Åland Islands"
  ],
  "DK": [
    "Capital Region", "Central Jutland", "South Denmark", "Zealand", "North Jutland"
  ],
  "BE": [
    "Brussels", "Antwerp", "East Flanders", "Flemish Brabant", "Hainaut", "Liège",
    "Limburg", "Luxembourg", "Namur", "Walloon Brabant", "West Flanders"
  ]
}; 
 