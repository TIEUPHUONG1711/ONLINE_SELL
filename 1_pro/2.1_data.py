import pandas as pd 
import matplotlib.pyplot as plt

d = pd.read_csv(r"D:\DATA_ANALYST\project\1_pro\1_online_retail.csv")

def clean_data(d):
    d = d.copy()
    d["InvoiceDate"] = pd.to_datetime(d["InvoiceDate"])
    d["CustomerID"] = d["CustomerID"].astype("str")
    d = d[~d["InvoiceNo"].astype(str).str.startswith("C")]
    d = d[(d["Quantity"] > 0) & (d["UnitPrice"] > 0)]
    d["CustomerID"] = d["CustomerID"].fillna("Unknown")
    d["Description"] = d["Description"].fillna("Unknown")
    d["TotalPrice"] = d["Quantity"] * d["UnitPrice"]
    return d 

d = clean_data(d)
d.to_csv(r"D:\DATA_ANALYST\project\1_pro\clean_data.csv", index=False)

def add_time_features(d,fred = "M"):
    d = d.copy()
    d["Period"] = d["InvoiceDate"].dt.to_period(fred)
    return d 

def build_kpi(d):
    d = d.copy()
    kpi = d.groupby("Period", as_index= False).agg(
        TotalRevenue = ("TotalPrice","sum"),
        TotalCustomer = ("CustomerID","nunique"),
        TotalOrder = ("InvoiceNo","nunique")
    )
    kpi["AOV"] = kpi["TotalRevenue"]/kpi["TotalOrder"]
    
    return kpi
d = clean_data(d)
d = add_time_features(d,fred = "M")
kpi = build_kpi(d)
print(kpi["TotalRevenue"].sum())
kpi.to_csv(r"D:\DATA_ANALYST\project\1_pro\kpi.csv", index=False)
# fig,ax = plt.subplots(1,2,figsize=(10,12))
# kpi["TotalRevenue"].plot(kind="line", title="Total Revenue Over Time", ax=ax[0])
# kpi["TotalCustomer"].plot(kind="line", ax=ax[1])
# kpi["AOV"].plot(kind="line", ax=ax[1])
# ax[1].set_title("Total Customer & AOV Over Time")
# plt.legend()
# plt.show()

# => nhìn vào biểu đồ ta thấy: doanh thu giảm sâu từ tháng 11 đến tháng 12
# => nguyên nhân là do số lượng khác hàng giảm mạnh từ tháng 11 đến tháng 12, trong khi AOV không thay đổi nhiều, điều này cho thấy khách hàng vẫn chi tiêu bình thường nhưng số lượng khách hàng giảm mạnh đã dẫn đến doanh thu giảm sâu    

#vậy khách hàng giảm mạnh là khách cũ hay mới? 
def customer_type(d):
    d = d.copy()
    First_purchase = d.groupby("CustomerID")["InvoiceDate"].min()
    d["FirstPurchaseDate"] = d["CustomerID"].map(First_purchase)
    
    d["CustomerType"] = (d["InvoiceDate"].dt.to_period("M") == d["FirstPurchaseDate"].dt.to_period("M"))
    d["CustomerType"] = d["CustomerType"].map({True:"New", False:"Existing"})
    return d

d = customer_type(d)


def customer_trend(d):
    d = d.copy()
    total = d.groupby("Period")["CustomerID"].nunique()
    #sau dòng này period sẽ là index, CustomerID sẽ là giá trị, thể hiện số lượng khách hàng theo từng tháng
    new = d[d["CustomerType"]=="New"].groupby("Period")["CustomerID"].nunique()
    trend = pd.DataFrame({"Total":total, "New":new})
    #nếu là 2 dataframe phải dùng merge để gộp lại, còn ở đây total và new đều có cùng index là Period nên ta có thể tạo dataframe mới bằng cách truyền vào 2 series này, pandas sẽ tự động gộp lại theo index Period
    trend["Existing"] = trend["Total"] - trend["New"]
    trend = trend.reset_index()
    return trend

trend = customer_trend(d)
trend.to_csv(r"D:\DATA_ANALYST\project\1_pro\customer_trend.csv", index=False)
# trend[["New","Existing"]].plot(kind="line", title="Customer Trend Over Time")
# plt.show()

# => nhìn vào biểu đồ ta thấy khách hàng cũ và mới đều giảm mạnh, nhưng khách hàng cũ giảm mạnh hơn, điều này cho thấy nguyên nhân chính dẫn đến doanh thu giảm sâu là do khách hàng cũ giảm mạnh
#vậy khách hàng cũ của tháng 12 giảm mạnh ở quốc gia nào và sản phẩm nào?

def top_drop(d,group_col,target_period):
    d = d.copy()
    temp = d.groupby(["Period", group_col])["CustomerID"].nunique().reset_index()
    temp = temp.sort_values([group_col, "Period"])
    temp["Prev"] = temp.groupby(group_col)["CustomerID"].shift(1)
    temp["Change"] = temp["CustomerID"] - temp["Prev"]
    temp = temp[temp["Period"] == target_period]
    top_drop = temp.sort_values("Change").head(10)    
    
    return top_drop

top_country = top_drop(d, "Country", "2011-12")
top_product = top_drop(d, "Description", "2011-12")
fig,ax = plt.subplots(1,2,figsize=(7,3))
top_country.plot(kind="bar", x="Country", y="Change", title="Top Country Drop in Dec 2011", ax=ax[0])
top_product.plot(kind="bar", x="Description", y="Change", title="Top Product Drop in Dec 2011", ax=ax[1])
plt.show()

top_country.to_csv(r"D:\DATA_ANALYST\project\1_pro\top_country_drop.csv", index=False)
top_product.to_csv(r"D:\DATA_ANALYST\project\1_pro\top_product_drop.csv", index=False)


#=> nhìn vào biểu đồ ta thấy khách hàng cũ giảm mạnh nhất ở UK, Germany và France,
# sản phẩm giảm mạnh nhất là Rabbit night light

