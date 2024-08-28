package THJava.Bai2;

public class tessTG {
	public static void main(String[] args) {
		Diem A = new Diem();
		Diem B = new Diem(3,0);
		Diem C = new Diem(0,4);
		
		TamGiac ABC = new TamGiac(A,B,C);
		
		System.out.println("Dien tich: " + ABC.dienTich());
		System.out.println("Chu vi: " + ABC.chuVi());
	}
}
