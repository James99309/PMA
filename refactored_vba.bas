Option Explicit

' 常量定义
Private Const SCORE_DESIGN_INSTITUTE As Integer = 10
Private Const SCORE_DEALER As Integer = 20
Private Const SCORE_INTEGRATOR As Integer = 50
Private Const SCORE_USER As Integer = 30

' 项目类型常量
Private Const PROJECT_TYPE_SALES_FOCUS As String = "销售重点"
Private Const PROJECT_TYPE_CHANNEL_FOLLOW As String = "渠道跟进"
Private Const PROJECT_TYPE_DESIGN_INSTITUTE As String = "设计院阶段"

' 来源类型常量
Private Const SOURCE_TYPE_DESIGN_INSTITUTE As String = "设计院"
Private Const SOURCE_TYPE_DEALER As String = "经销商"
Private Const SOURCE_TYPE_INTEGRATOR As String = "系统集成商"
Private Const SOURCE_TYPE_USER As String = "用户"

' 列索引常量
Private Const COL_PROJECT_ID As Integer = 1
Private Const COL_PROJECT_TYPE As Integer = 2
Private Const COL_COMPANY_EVALUATION As Integer = 3
Private Const COL_DESIGN As Integer = 4
Private Const COL_DEALER As Integer = 5
Private Const COL_INTEGRATOR As Integer = 6

' 主函数：更新项目和积分
Public Sub UpdateProjectsAndScore()
    Dim ws As Worksheet
    Dim projectTable As ListObject
    Dim scoreTable As ListObject
    
    ' 初始化工作表对象
    Set ws = ThisWorkbook.Sheets("CaculatePoint")
    Set projectTable = ws.ListObjects(1)
    Set scoreTable = ThisWorkbook.Sheets("CalculateMap").ListObjects(1)
    
    ' 验证数据
    If Not ValidateTables(projectTable, scoreTable) Then
        MsgBox "数据验证失败，请检查数据完整性", vbExclamation
        Exit Sub
    End If
    
    ' 处理项目数据
    ProcessProjectData projectTable, scoreTable
    
    ' 更新积分
    UpdateScores projectTable, scoreTable
    
    MsgBox "项目和积分更新完成", vbInformation
End Sub

' 验证数据完整性
Private Function ValidateTables(projectTable As ListObject, scoreTable As ListObject) As Boolean
    ValidateTables = False
    
    If projectTable Is Nothing Or scoreTable Is Nothing Then
        MsgBox "找不到必要的数据表", vbExclamation
        Exit Function
    End If
    
    If projectTable.ListRows.Count = 0 Or scoreTable.ListRows.Count = 0 Then
        MsgBox "数据表为空", vbExclamation
        Exit Function
    End If
    
    ValidateTables = True
End Function

' 处理项目数据
Private Sub ProcessProjectData(projectTable As ListObject, scoreTable As ListObject)
    Dim row As ListRow
    Dim projectType As String
    Dim sourceType As String
    Dim score As Integer
    
    ' 对项目表进行排序
    SortProjectTable projectTable
    
    ' 处理每个项目
    For Each row In projectTable.ListRows
        projectType = row.Range.Cells(1, COL_PROJECT_TYPE).Value
        sourceType = row.Range.Cells(1, COL_COMPANY_EVALUATION).Value
        
        ' 计算项目积分
        score = CalculateProjectScore(projectType, sourceType)
        
        ' 更新积分
        row.Range.Cells(1, COL_PROJECT_ID).Value = score
    Next row
End Sub

' 计算项目积分
Private Function CalculateProjectScore(projectType As String, sourceType As String) As Integer
    Dim baseScore As Integer
    
    ' 根据项目类型计算基础积分
    Select Case projectType
        Case PROJECT_TYPE_SALES_FOCUS
            baseScore = 50
        Case PROJECT_TYPE_CHANNEL_FOLLOW
            baseScore = 30
        Case PROJECT_TYPE_DESIGN_INSTITUTE
            baseScore = 100
        Case Else
            baseScore = 0
    End Select
    
    ' 根据来源类型计算额外积分
    Select Case sourceType
        Case SOURCE_TYPE_DESIGN_INSTITUTE
            baseScore = baseScore + SCORE_DESIGN_INSTITUTE
        Case SOURCE_TYPE_DEALER
            baseScore = baseScore + SCORE_DEALER
        Case SOURCE_TYPE_INTEGRATOR
            baseScore = baseScore + SCORE_INTEGRATOR
        Case SOURCE_TYPE_USER
            baseScore = baseScore + SCORE_USER
    End Select
    
    CalculateProjectScore = baseScore
End Function

' 对项目表进行排序
Private Sub SortProjectTable(table As ListObject)
    With table.Sort
        .SortFields.Clear
        .SortFields.Add _
            Key:=table.ListColumns(1).DataBodyRange, _
            SortOn:=xlSortOnValues, _
            Order:=xlDescending
        .Header = xlYes
        .MatchCase = False
        .Orientation = xlTopToBottom
        .SortMethod = xlPinYin
        .Apply
    End With
End Sub

' 更新积分
Private Sub UpdateScores(projectTable As ListObject, scoreTable As ListObject)
    Dim row As ListRow
    Dim totalScore As Integer
    
    ' 计算总积分
    For Each row In projectTable.ListRows
        totalScore = totalScore + row.Range.Cells(1, COL_PROJECT_ID).Value
    Next row
    
    ' 更新积分表
    With scoreTable.ListRows.Add
        .Range.Cells(1, 1).Value = "总积分"
        .Range.Cells(1, 2).Value = totalScore
    End With
End Sub 