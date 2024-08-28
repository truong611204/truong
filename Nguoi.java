package bai03;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Scanner;

public class Nguoi {
	protected String hoTen;
	protected Date ngaySinh;
	protected String queQuan;
	
	public Nguoi() {}
	
	public Nguoi(String hoTen, Date ngaySinh) {
		this.hoTen = hoTen;
		this.ngaySinh = ngaySinh;
	}
	
	public Nguoi(String hoTen, Date ngaySinh, String queQuan) {
		this(hoTen, ngaySinh);
		this.queQuan = queQuan;
	}
	
	public void nhapThongTin(Scanner sc) {
		System.out.println("Nhap ho ten: ");
		this.hoTen = sc.nextLine();
		System.out.print("Nhap ngay sinh (dd/mm/yyyy): ");
		String ngaySinhStr = sc.nextLine();
	    this.ngaySinh = stringToDate(ngaySinhStr);
	    System.out.print("Nhap que quan: ");
	    this.queQuan = sc.nextLine();
	}
	
	private Date stringToDate(String ngaySinhStr) {
		SimpleDateFormat sdf = new SimpleDateFormat("dd/mm/yyyy");
	       Date ngaySinhDate = null;
	       try{
	        ngaySinhDate = sdf.parse(ngaySinhStr);
	       }catch(Exception ex){
	           System.out.println("Loi dinh dang ngay sinh");
	       }
	    return ngaySinhDate;
	}

	public void inThongTin(){
		 System.out.println("Ho ten: " + hoTen);
	     System.out.println("Ngay sinh: " + ngaySinh);
	     System.out.println("Que quan: " + queQuan);
	}
	public static void main(String[] args) {
		Scanner sc = new Scanner(System.in);
		Nguoi ng = new Nguoi();
		ng.nhapThongTin(sc);
		ng.inThongTin();
	}
}
