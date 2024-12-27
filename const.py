"""Constants for the eSolat Takwim Malaysia integration."""
from datetime import timedelta
from zoneinfo import ZoneInfo

DOMAIN = "esolattakwim"
SCAN_INTERVAL = timedelta(days=1)
TIMEZONE = ZoneInfo("Asia/Kuala_Lumpur")

# API endpoints
ISLAMIC_EVENTS_API = "https://www.e-solat.gov.my/index.php?r=esolatApi/islamicevent&type=all"
HIJRI_API = "https://www.e-solat.gov.my/index.php?r=esolatApi/tarikhtakwim&period=today&datetype=miladi"
PRAYER_TIMES_API = "https://www.e-solat.gov.my/index.php?r=esolatApi/takwimsolat&period=year&zone={zone}"

# Prayer names mapping
PRAYER_NAMES = {
    "imsak": "Imsak",
    "fajr": "Fajr",
    "syuruk": "Syuruk",
    "dhuhr": "Dhuhr",
    "asr": "Asr",
    "maghrib": "Maghrib",
    "isha": "Isha"
}

HIJRI_MONTHS = {
    "01": "Muharram",
    "02": "Safar",
    "03": "Rabi'ul Awwal",
    "04": "Rabi'ul Akhir",
    "05": "Jamadil Awwal",
    "06": "Jamadil Akhir",
    "07": "Rejab",
    "08": "Sha'aban",
    "09": "Ramadhan",
    "10": "Syawal",
    "11": "Zulkaedah",
    "12": "Zulhijjah"
}

# Zone codes and names
ZONES = {
    "jhr01": "JHR01 - Pulau Aur dan Pulau Pemanggil",
    "jhr02": "JHR02 - Kota Tinggi, Mersing, Johor Bahru",
    "jhr03": "JHR03 - Kluang, Pontian",
    "jhr04": "JHR04 - Batu Pahat, Muar, Segamat, Gemas",
    "kdh01": "KDH01 - Kota Setar, Kubang Pasu, Pokok Sena",
    "kdh02": "KDH02 - Pendang, Kuala Muda, Yan",
    "kdh03": "KDH03 - Padang Terap, Sik",
    "kdh04": "KDH04 - Baling",
    "kdh05": "KDH05 - Kulim, Bandar Baharu",
    "kdh06": "KDH06 - Langkawi",
    "kdh07": "KDH07 - Gunung Jerai",
    "ktn01": "KTN01 - K.Bharu,Bachok,Pasir Puteh,Tumpat,Pasir Mas,Tnh. Merah,Machang,Kuala Krai,Mukim Chiku",
    "ktn03": "KTN03 - Jeli, Gua Musang (Mukim Galas, Bertam)",
    "mlk01": "MLK01 - Seluruh Negeri Melaka",
    "ngs01": "NGS01 - Tampin, Jempol",
    "ngs02": "NGS02 - Port Dickson, Seremban, Kuala Pilah, Jelebu, Rembau",
    "phg01": "PHG01 - Pulau Tioman",
    "phg02": "PHG02 - Kuantan, Pekan, Rompin, Muadzam Shah",
    "phg03": "PHG03 - Maran, Chenor, Temerloh, Bera, Jerantut",
    "phg04": "PHG04 - Bentong, Raub, Kuala Lipis",
    "phg05": "PHG05 - Genting Sempah, Janda Baik, Bukit Tinggi",
    "phg06": "PHG06 - Cameron Highlands, Bukit Fraser",
    "prk01": "PRK01 - Tapah,Slim River, Tanjung Malim",
    "prk02": "PRK02 - Ipoh, Batu Gajah, Kampar, Sg. Siput, Kuala Kangsar",
    "prk03": "PRK03 - Pengkalan Hulu, Grik, Lenggong",
    "prk04": "PRK04 - Temengor, Belum",
    "prk05": "PRK05 - Teluk Intan, Bagan Datuk, Kg.Gajah,Sri Iskandar, Beruas,Parit,Lumut,Setiawan",
    "prk06": "PRK06 - Selama, Taiping, Bagan Serai, Parit Buntar",
    "prk07": "PRK07 - Bukit Larut",
    "pls01": "PLS01 - Kangar, Padang Besar, Arau",
    "sbh01": "SBH01 - Zon 1 - Sandakan, Bdr. Bkt. Garam, Semawang, Temanggong, Tambisan",
    "sbh02": "SBH02 - Zon 2 - Pinangah, Terusan, Beluran, Kuamut, Telupid",
    "sbh03": "SBH03 - Zon 3 - Lahad Datu, Kunak, Silabukan, Tungku, Sahabat, Semporna",
    "sbh04": "SBH04 - Zon 4 - Tawau, Balong, Merotai, Kalabakan",
    "sbh05": "SBH05 - Zon 5 - Kudat, Kota Marudu, Pitas, Pulau Banggi",
    "sbh06": "SBH06 - Zon 6 - Gunung Kinabalu",
    "sbh07": "SBH07 - Zon 7 - Papar, Putatan, Penampang, Kota Kinabalu",
    "sbh08": "SBH08 - Zon 8 - Pensiangan, Keningau, Tambunan, Nabawan",
    "sbh09": "SBH09 - Zon 9 - Sipitang, Membakut, Beaufort, Kuala Penyu, Weston, Tenom, Long Pa Sia",
    "sgr01": "SGR01 - Gombak,H.Selangor,Rawang,H.Langat,Sepang,Petaling,S.Alam",
    "sgr02": "SGR02 - Sabak Bernam, Kuala Selangor, Klang, Kuala Langat",
    "sgr03": "SGR03 - Kuala Lumpur",
    "sgr04": "SGR04 - Putrajaya",
    "srw01": "SRW01 - Zon 1 - Limbang, Sundar, Trusan",
    "srw02": "SRW02 - Zon 2 - Miri, Niah, Bekenu, Sibuti, Marudi",
    "srw03": "SRW03 - Zon 3 - Layar,Betong,Spaoh,Pusa,Saratok,Roban,Debak",
    "srw04": "SRW04 - Zon 4 - Igan,Kanowit,Sibu,Dalat,Oya",
    "srw05": "SRW05 - Zon 5 - Belawai,Matu,Daro,Sarikei,Julau,Bintangor,Rajang",
    "srw06": "SRW06 - Zon 6 - Kabong,Lingga,Sri Aman,Engkelili,Betong,Spaoh,Pusa,Saratok,Roban,Debak",
    "srw07": "SRW07 - Zon 7 - Samarahan,Simunjan,Serian,Sebuyau,Meludam",
    "srw08": "SRW08 - Zon 8 - Kuching,Bau,Lundu,Sematan",
    "srw09": "SRW09 - Zon 9 - Zon Khas (Kampung Patarikan)",
    "trg01": "TRG01 - Kuala Terengganu, Marang, Kuala Nerus",
    "trg02": "TRG02 - Besut, Setiu",
    "trg03": "TRG03 - Hulu Terengganu",
    "trg04": "TRG04 - Dungun, Kemaman",
    "wly01": "WLY01 - Labuan",
    "wly02": "WLY02 - Putrajaya"
}