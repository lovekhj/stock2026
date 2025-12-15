import os

class FileManager:
    def __init__(self):
        self.current_path = os.getcwd()
    
    def make_folder(self, today):
        """
        지정된 날짜로 폴더를 생성합니다.
        
        Args:
            today (str): 생성할 폴더명 (날짜 형식: YYYYMMDD)
            
        Returns:
            str: 생성된 폴더의 전체 경로
        """
        folder_path = os.path.join(self.current_path, today)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"폴더 생성됨: {folder_path}")
        else:
            print(f"이미 존재하는 폴더: {folder_path}")

        return folder_path

    def check_and_delete_file(self, filename):
        """
        파일이 존재하는지 확인하고 있다면 삭제합니다.
        
        Args:
            filename (str): 확인할 파일의 경로
        """
        if os.path.isfile(filename):
            os.remove(filename)
            print(f"{filename} 파일을 삭제했습니다.")
        else:
            print(f"{filename} 파일이 존재하지 않습니다.")
    
    def get_current_path(self):
        """
        현재 작업 경로를 반환합니다.
        
        Returns:
            str: 현재 작업 경로
        """
        return self.current_path
    
    def set_current_path(self, path):
        """
        작업 경로를 변경합니다.
        
        Args:
            path (str): 변경할 경로
        """
        if os.path.exists(path):
            self.current_path = path
            print(f"작업 경로가 변경되었습니다: {path}")
        else:
            raise ValueError(f"존재하지 않는 경로입니다: {path}")

# 사용 예시
if __name__ == "__main__":
    # FileManager 인스턴스 생성
    file_manager = FileManager()
    
    # 폴더 생성 테스트
    today = "20250222"
    folder_path = file_manager.make_folder(today)
    
    # 파일 체크 및 삭제 테스트
    test_file = os.path.join(folder_path, "test.txt")
    file_manager.check_and_delete_file(test_file)