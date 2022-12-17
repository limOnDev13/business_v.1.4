import numpy as np
import matplotlib.pyplot as plt
import datetime as date
import copy
from ctypes import *


class DistributionParameters():
    # среднеквадратичное отклонение
    scale = 0
    # средний коэффициент массонакопления
    massAccumulationCoefficient = 0
    # количество рыб
    amountFishes = 0
    # массив значений, которые распределены по Гауссу в заданных параметрах
    _gaussValues = []

    def __init__(self, amountFishes,
                 scale=0.003,
                 massAccumulationCoefficientMin=0.07,
                 massAccumulationCoefficientMax=0.087):
        self.massAccumulationCoefficient = (massAccumulationCoefficientMin +
                                       massAccumulationCoefficientMax) / 2
        self.amountFishes = amountFishes
        self.scale = scale
        self._make_gaussian_distribution()

    def _make_gaussian_distribution(self):
        self._gaussValues = np.random.normal(self.massAccumulationCoefficient,
                                        self.scale,
                                        self.amountFishes)
        self._gaussValues.sort()

    def draw_hist_distribution(self, numberFishInOneColumn):
        plt.hist(self._gaussValues, numberFishInOneColumn)
        plt.show()

    def return_array_distributed_values(self):
        return self._gaussValues


def assemble_array(array, amountItems, index):
    result = (c_float * amountItems)()
    for i in range(amountItems):
        result[i] = array[i][index]
    return result


def calculate_end_date_of_month(startDate):
    '''
    result = startDate
    while ((result.day != startDate.day) or
           (result.month == startDate.month)):
        result += date.timedelta(1)
    '''
    month = startDate.month + 1
    year = startDate.year
    if (year > 2100):
        print('Опять ошибка с датами((((((((((((((((((((((((((((')
    if (month > 12):
        month = 1
        year += 1
    result = date.date(year, month, startDate.day)
    return result


def draw_line(start, end, step, current):
    amount = int((end - start) / step) + 1
    percent = current / amount * 100
    print(int(percent), '%')


class FishArray():
    _amountFishes = 0
    _arrayFishes = list()
    _biomass = c_float()
    # массив покупок мальков
    _arrayFryPurchases = list()
    _feedRatio = 1.5
    _dllBuisnessPlan = 0


    def __init__(self, feedRatio=1.5):
        self._feedRatio = c_float(feedRatio)
        self._biomass = c_float()
        self._amountFishes = 0
        self._arrayFishes = list()
        self._arrayFryPurchases = list()
        self._dllBuisnessPlan = WinDLL('D:/github/business_v1.3/Project1/x64/Debug/dllArrayFish.dll')

    def add_biomass(self, date, amountFishes, averageMass):
        # создаем параметры для нормального распределения коэффициентов массонакопления
        distributionParameters = DistributionParameters(amountFishes)
        arrayCoefficients = distributionParameters.return_array_distributed_values()

        # закидываем информацию о новой биомассе в массив
        for i in range(amountFishes):
            # ноль означает (количество дней в бассике, но это не точно
            # arrayFishes = [[startingMass, massAccumulationCoefficient, currentMass],...]
            self._arrayFishes.append([averageMass, arrayCoefficients[i], averageMass])
            self._arrayFryPurchases.append([date, amountFishes, averageMass])

        # увеличиваем количество рыбы в бассейне
        self._amountFishes += amountFishes
        # так как все в граммах, то делим на 1000, чтобы получить килограммы в биомассе
        self._biomass.value += amountFishes * averageMass / 1000

    def add_other_FishArrays(self, fishArray):
        amountNewFishes = len(fishArray)

        # arrayFishes = [[startingMass, massAccumulationCoefficient, currentMass]
        for i in range(amountNewFishes):
            self._biomass.value = self._biomass.value + fishArray[i][2] / 1000
            self._arrayFishes.append(fishArray[i])
        self._amountFishes += amountNewFishes

    def _sort_fish_array(self):
        self._arrayFishes.sort(key=lambda x: x[2])

    def remove_biomass(self, amountFishToRemove):
        self._sort_fish_array()
        removedFishes = list()
        for i in range(amountFishToRemove):
            fish = self._arrayFishes.pop(self._amountFishes - amountFishToRemove)
            removedFishes.append(fish)
            # уменьшаем биомассу
            self._biomass.value -= fish[2] / 1000
        # уменьшаем количество рыб
        self._amountFishes -= amountFishToRemove
        return removedFishes

    def daily_work(self):
        # подготовим переменные для использования ctypes
        dailyWorkLib = self._dllBuisnessPlan.daily_work

        dailyWorkLib.argtypes = [POINTER(c_float), POINTER(c_float),
                                 c_int, c_float, POINTER(c_float)]
        dailyWorkLib.restype = c_float

        # соберем массивы масс и коэффициентов массонакопления
        arrayMass = assemble_array(self._arrayFishes, self._amountFishes, 2)
        arrayMassAccumulationCoefficient = assemble_array(self._arrayFishes,
                                                          self._amountFishes, 1)

        dailyFeedMass = dailyWorkLib(arrayMass, arrayMassAccumulationCoefficient,
                                     self._amountFishes, self._feedRatio,
                                     byref(self._biomass))

        for i in range(self._amountFishes):
            self._arrayFishes[i][2] = arrayMass[i]

        return dailyFeedMass

    def do_daily_work_some_days(self, amountDays):
        # подготовим переменные для использования ctypes
        dailyWorkLib = self._dllBuisnessPlan.do_daily_work_some_days

        dailyWorkLib.argtypes = [POINTER(c_float), POINTER(c_float),
                                 c_int, c_float, POINTER(c_float), c_int]
        dailyWorkLib.restype = c_float

        # соберем массивы масс и коэффициентов массонакопления
        arrayMass = assemble_array(self._arrayFishes, self._amountFishes, 2)
        arrayMassAccumulationCoefficient = assemble_array(self._arrayFishes,
                                                          self._amountFishes, 1)

        totalFeedMass = dailyWorkLib(arrayMass, arrayMassAccumulationCoefficient,
                                     self._amountFishes, self._feedRatio,
                                     byref(self._biomass), amountDays)

        for i in range(self._amountFishes):
            self._arrayFishes[i][2] = arrayMass[i]

        return totalFeedMass

    def get_amount_fishes(self):
        return self._amountFishes

    def get_array_fish(self):
        return self._arrayFishes

    def calculate_when_fish_will_be_sold(self, massComercialFish,
                                         singleVolume, fishArray):
        # подготовим переменные для использования ctypes
        calculateLib = self._dllBuisnessPlan.calculate_when_fish_will_be_sold

        calculateLib.argtypes = [POINTER(c_float), POINTER(c_float),
                                 c_int, c_float, POINTER(c_float),
                                 c_float, c_int]
        calculateLib.restype = c_int

        amountFish = len(fishArray)
        biomass = 0
        for i in range(amountFish):
            biomass += fishArray[i][2] / 1000
        biomass = c_float(biomass)

        # соберем массивы масс и коэффициентов массонакопления
        arrayMass = assemble_array(fishArray, amountFish, 2)
        arrayMassAccumulationCoefficient = assemble_array(fishArray,
                                                          amountFish, 1)

        amountDays = calculateLib(arrayMass, arrayMassAccumulationCoefficient,
                                  amountFish, self._feedRatio,
                                  byref(biomass), massComercialFish,
                                  singleVolume)

        for i in range(amountFish):
            fishArray[i][2] = arrayMass[i]

        return amountDays

    def calculate_difference_between_number_growth_days_and_limit_days(self, massComercialFish, singleVolume,
                                                                       maxDensity, square):
        calculateLib = self._dllBuisnessPlan.calculate_how_many_fish_needs

        calculateLib.argtypes = [POINTER(c_float), POINTER(c_float),
                                 POINTER(c_float), c_int, c_float,
                                 POINTER(c_float),  POINTER(c_float),
                                 c_float, c_int, c_float, c_float,
                                 POINTER(c_int)]
        calculateLib.restype = c_int

        # соберем массивы масс и коэффициентов массонакопления
        arrayMass1 = assemble_array(self._arrayFishes, self._amountFishes, 2)
        arrayMass2 = assemble_array(self._arrayFishes, self._amountFishes, 2)
        arrayMassAccumulationCoefficient = assemble_array(self._arrayFishes,
                                                          self._amountFishes, 1)
        resultAmountsDays = (c_int * 2)(0)

        biomass1 = c_float(0.0)
        biomass2 = c_float(0.0)

        for i in range(self._amountFishes):
            biomass1.value += arrayMass1[i] / 1000
            biomass2.value += arrayMass1[i] / 1000

        amountDays = calculateLib(arrayMass1, arrayMass2, arrayMassAccumulationCoefficient,
                                  self._amountFishes, self._feedRatio,
                                  byref(biomass1), byref(biomass2), massComercialFish,
                                  singleVolume, maxDensity, square, resultAmountsDays)

        return [amountDays, resultAmountsDays[0], resultAmountsDays[1]]
    def calculate_average_mass(self):
        self.update_biomass()
        if (self._amountFishes != 0):
            result = self._biomass.value / self._amountFishes * 1000
        else:
            result = 0.0
        return result

    def update_biomass(self):
        result = 0
        for i in range(self._amountFishes):
            result += self._arrayFishes[i][2] / 1000
        self._biomass.value = result

    def get_biomass(self):
        return self._biomass.value

    def get_three_fish(self):
        result = [[self._arrayFishes[0][1], self._arrayFishes[0][2]]]
        middle = int(self._amountFishes / 2)
        result.append([self._arrayFishes[middle][1], self._arrayFishes[middle][2]])
        end = self._amountFishes - 1
        result.append([self._arrayFishes[end][1], self._arrayFishes[end][2]])
        return result


class Pool():
    square = 0
    maxPlantingDensity = 0
    arrayFishes = 0
    # количество мальков в 1 упаковке
    singleVolumeFish = 0
    # цена на мальков
    costFishFry = [[5, 35],
                   [10, 40],
                   [20, 45],
                   [30, 50],
                   [50, 60],
                   [100, 130]]
    # массив, в котором хранится информация о покупке мальков
    arrayFryPurchases = list()
    # массив, в котором хранится информация о продаже рыбы
    arraySoldFish = list()
    # текущая плотность посадки
    currentDensity = 0
    # массив кормежек
    feeding = list()
    # масса товарной рыбы
    massComercialFish = 400
    # цена рыбы
    price = 1000
    # индекс зарыбления
    indexFry = 0
    procentOnDepreciationEquipment = 10
    poolHistory = list()


    def __init__(self, square, singleVolumeFish=100, price=850,
                 massComercialFish=400,
                 maximumPlantingDensity=40):
        self.square = square
        self.massComercialFish = massComercialFish
        self.maxPlantingDensity = maximumPlantingDensity
        self.singleVolumeFish = singleVolumeFish
        self.arrayFishes = FishArray()
        self.feeding = list()
        self.arrayFryPurchases = list()
        self.arraySoldFish = list()
        self.poolHistory = list()
        self.price = price

    def add_new_biomass(self, amountFishes, averageMass, newIndex, date):
        self.indexFry = newIndex
        self.arrayFishes.add_biomass(date, amountFishes, averageMass)
        # сохраним инфо о покупки мальков
        # arrayFryPurchases[i] = [date, amountFries, averageMass, totalPrice]
        totalPrice = 0
        for i in range(1, len(self.costFishFry)):
            if (self.costFishFry[i - 1][0] < averageMass <= self.costFishFry[i][0]):
                totalPrice = amountFishes * self.costFishFry[i][1]
                break
            elif (averageMass > 200):
                totalPrice = amountFishes * averageMass
                break
        self.arrayFryPurchases.append([date, amountFishes, averageMass, totalPrice])
        self.currentDensity = amountFishes * (averageMass / 1000) / self.square

    def daily_growth(self, day, saveInfo):
        todayFeedMass = self.arrayFishes.daily_work()
        # сохраняем массы кормежек
        self.feeding.append([day, todayFeedMass])

        # проверяем, есть ли рыба на продажу, и если есть - продаем
        self.sell_fish(day)
        if (saveInfo):
            # [день, количество рыбы, биомасса, средняя масса, плотность]
            self.poolHistory.append([day, self.arrayFishes.get_amount_fishes(), self.arrayFishes.get_biomass(),
                                     self.arrayFishes.calculate_average_mass(), self.update_density()])

    def sell_fish(self, day):
        amountFishForSale = 0
        for i in range(self.arrayFishes.get_amount_fishes()):
            if (self.arrayFishes.get_array_fish()[i][2] >= self.massComercialFish):
                amountFishForSale += 1

        if ((amountFishForSale >= self.singleVolumeFish) or
                ((amountFishForSale == self.arrayFishes.get_amount_fishes()) and
                 (self.arrayFishes.get_amount_fishes() != 0))):
            previousBiomass = self.arrayFishes.get_biomass()
            soldFish = self.arrayFishes.remove_biomass(amountFishForSale)
            # продаем выросшую рыбу и сохраняем об этом инфу
            soldBiomass = 0
            amountSoldFish = 0
            for i in range(len(soldFish)):
                soldBiomass += soldFish[i][2] / 1000
                amountSoldFish += 1

            revenue = soldBiomass * self.price

            self.arraySoldFish.append([day, amountSoldFish, soldBiomass, revenue])
            # обновим density
            self.currentDensity = self.arrayFishes.get_biomass() / self.square
            '''
            print(day, ' indexFry = ', self.indexFry, ' было ', previousBiomass, ' продано: ', soldBiomass,
                  ' стало ', self.arrayFishes.get_biomass(), ' выручка: ', revenue)
            '''

    def update_density(self):
        self.currentDensity = self.arrayFishes.get_biomass() / self.square
        return self.currentDensity

    def calculate_difference_between_number_growth_days_and_limit_days(self, amountFishForSale):
        testFishArray = copy.deepcopy(self.arrayFishes)
        amountDays = testFishArray.calculate_difference_between_number_growth_days_and_limit_days\
            (self.massComercialFish,
             amountFishForSale,
             self.maxPlantingDensity,
             self.square)
        return amountDays


class Opimization():
    _dllArrayFish = 0
    _dllPool = 0
    masses = list()
    mainVolueFish = 0
    amountModules = 2
    amountPools = 4
    poolSquare = 10
    correctionFactor = 2
    feedPrice = 260
    workerSalary = 40000
    amountWorkers = 2
    cwsdCapacity = 5.5
    electricityCost = 3.17
    rent = 100000
    costCWSD = 3000000
    depreciationReservePercent = 7.5
    expansionReservePercent = 7.5
    credit = 500000
    annualPercentage = 15
    amountCreditMonth = 12
    grant = 5000000
    fishPrice = 850
    massCommercialFish = 400

    def __init__(self, masses, mainVolueFish, amountModules=2, amountPools=4,
            poolSquare=10, correctionFactor=2, feedPrice=260,
            workerSalary=40000, amountWorkers=2, cwsdCapacity=5.5,
            electricityCost=3.17, rent=100000, costCWSD=3000000, depreciationReservePercent=7.5,
            expansionReservePercent=7.5, credit=500000, annualPercentage=15, amountCreditMonth=12,
            grant=5000000, fishPrice=850, massCommercialFish=400):
        self.masses = masses
        self.amountModules = amountModules
        self.amountPools = amountPools
        self.poolSquare = poolSquare
        self.correctionFactor = correctionFactor
        self.feedPrice = feedPrice
        self.workerSalary = workerSalary
        self.amountWorkers = amountWorkers
        self.cwsdCapacity = cwsdCapacity
        self.electricityCost = electricityCost
        self.rent = rent
        self.costCWSD = costCWSD
        self.depreciationReservePercent = depreciationReservePercent
        self.expansionReservePercent = expansionReservePercent
        self.credit = credit
        self.annualPercentage = annualPercentage
        self.amountCreditMonth = amountCreditMonth
        self.grant = grant
        self.fishPrice = fishPrice
        self.massCommercialFish = massCommercialFish
        self.mainVolueFish = mainVolueFish

        self._dllPool = WinDLL("D:/github/buisnessPlan_v1.2.1/buisnessPlan_v1.2/dllPool/x64/Debug/dllPool.dll")
        self._dllArrayFish = WinDLL('D:/github/business_v1.3/Project1/x64/Debug/dllArrayFish.dll')

    def calculate_optimized_amount_fish_in_commercial_pool(self, square, startMass, mass, startAmount, step):
        flagNumber = 0
        amountFish = startAmount
        amountGrowthDays = 0
        amountDaysBeforeLimit = 0

        while (flagNumber >= 0):
            pool = Pool(square, startMass)
            pool.add_new_biomass(amountFish, mass, 0, date.date.today())
            x = pool.calculate_difference_between_number_growth_days_and_limit_days(amountFish)
            flagNumber = x[0]
            if (flagNumber >= 0):
                amountFish += step
                amountGrowthDays = x[1]
                amountDaysBeforeLimit = x[2]

        return [amountFish, amountGrowthDays, amountDaysBeforeLimit]

    def calculate_max_average_mass(self, square, maxDensity, amountDays, startMass, step, amountFish, feedRatio):
        # подготовим переменные для использования ctypes
        calculateLib = self._dllArrayFish.calculate_density_after_some_days

        calculateLib.argtypes = [POINTER(c_float), POINTER(c_float),
                                 c_int, c_float, POINTER(c_float),
                                 c_int, c_float]
        calculateLib.restype = c_float

        currentMass = startMass
        currentDensity = 0
        while(currentDensity < maxDensity):
            # созданим объект FishArray
            fishArray = FishArray()
            fishArray.add_biomass(date.date.today(), amountFish, currentMass)
            # соберем массивы масс и коэффициентов массонакопления
            arrayMass = assemble_array(fishArray.get_array_fish(), amountFish, 2)
            arrayMassAccumulationCoefficient = assemble_array(fishArray.get_array_fish(),
                                                              amountFish, 1)

            biomass = c_float(0.0)
            for i in range(amountFish):
                biomass.value += arrayMass[i] / 1000

            currentDensity = calculateLib(arrayMass, arrayMassAccumulationCoefficient,
                                      amountFish, feedRatio,
                                      byref(biomass), amountDays,
                                      square)
            if (currentDensity < maxDensity):
                currentMass += step

        return currentMass

    def calculate_optimal_deltaMass(self, startDelta, step, endDelta, startDate, endDate, minMass, maxMass):
        delta = startDelta
        max = 0
        result = delta
        encounter = 1
        while (delta <= endDelta):
            cwsd = CWSD(self.masses, self.mainVolueFish, self.amountModules, self.amountPools,
                        self.poolSquare, self.correctionFactor, self.feedPrice,
                        self.workerSalary, self.amountWorkers, self.cwsdCapacity,
                        self.electricityCost, self.rent, self.costCWSD, self.depreciationReservePercent,
                        self.expansionReservePercent, self.credit, self.annualPercentage, self.amountCreditMonth,
                        self.grant, self.fishPrice, self.massCommercialFish)
            cwsd.work_cwsd(startDate, endDate, 50, delta, minMass, maxMass)
            x = cwsd.calculate_result_business_plan(startDate, endDate, 100000)
            if (max < x):
                max = x
                result = delta
            delta += step
            draw_line(startDelta, endDelta, step, encounter)
            print([delta, x])
            encounter += 1
        return [result, max]

    def calculate_optimal_credit(self, startCredit, step, endCredit, startDate, endDate, minMass, maxMass):
        credit = startCredit
        min = 0
        result = credit
        encounter = 1
        while (credit <= endCredit):
            cwsd = CWSD(self.masses, self.mainVolueFish, self.amountModules, self.amountPools,
                        self.poolSquare, self.correctionFactor, self.feedPrice,
                        self.workerSalary, self.amountWorkers, self.cwsdCapacity,
                        self.electricityCost, self.rent, self.costCWSD, self.depreciationReservePercent,
                        self.expansionReservePercent, self.credit, self.annualPercentage, self.amountCreditMonth,
                        self.grant, self.fishPrice, self.massCommercialFish)
            cwsd.work_cwsd(startDate, endDate, 50, 50, minMass, maxMass)
            cwsd.calculate_result_business_plan(startDate, endDate, 100000)
            x = cwsd.find_minimal_budget()
            if ((x > 0) and (x > min)):
                min = x
                result = credit
            draw_line(startCredit, endCredit, step, encounter)
            print([credit, x])
            encounter += 1
            credit += step
        return [result, min]

    def calculate_max_cost_one_module_business(self, startDate, endDate,
                                                   amountSteps, costCWSD, grant,
                                               credit, amountCreditMonth, minMass, maxMass):
        maxCost = 0
        averageCost = 0
        for i in range(amountSteps):
            cwsd = CWSD(self.masses, self.mainVolueFish, self.amountModules, self.amountPools,
                        self.poolSquare, self.correctionFactor, self.feedPrice,
                        self.workerSalary, self.amountWorkers, self.cwsdCapacity,
                        self.electricityCost, self.rent, self.costCWSD, self.depreciationReservePercent,
                        self.expansionReservePercent, self.credit, self.annualPercentage, self.amountCreditMonth,
                        self.grant, self.fishPrice, self.massCommercialFish)
            cwsd.work_cwsd(startDate, endDate, 50, 50, minMass, maxMass)
            cwsd.calculate_result_business_plan(date.date.today(), date.date(2028, 1, 1), 100000)
            # эта величина покаывает, сколько мы затратим на био и тех - расходы
            otherCosts = grant + credit - costCWSD - cwsd.find_minimal_budget()
            # тогда стоимость запуска нового модуля
            # (не включая кредиты, так как деньги будем брать и старого узв)
            # составит
            costOneModule = costCWSD + otherCosts - cwsd.monthlyPayment * amountCreditMonth
            print(i, ' расчет, стоимость запуска:', costOneModule)
            if (maxCost < costOneModule):
                maxCost = costOneModule
            averageCost += costOneModule
        averageCost /= amountSteps
        print()
        print('Средняя стоимость запуска одного узв: ', averageCost)
        print('Максимальная стоимость запуска одного узв: ', maxCost)

    def _calculate_average_profit(self, startDate, endDate, amountSteps, reserve,
                                  deltaMass, minMass, maxMass, limitSalary, masses,
                                  mainVolueFish, amountModules=2, amountPools=4,
                                  poolSquare=10, correctionFactor=2, feedPrice=260,
                                  workerSalary=40000, amountWorkers=2, cwsdCapacity=5.5,
                                  electricityCost=3.17, rent=100000, costCWSD=3000000, depreciationReservePercent=7.5,
                                  expansionReservePercent=7.5, credit=500000, annualPercentage=15, amountCreditMonth=12,
                                  grant=5000000, fishPrice=850, massCommercialFish=400):
        result = 0
        for i in range(amountSteps):
            cwsd = CWSD(masses, mainVolueFish, amountModules, amountPools,
                        poolSquare, correctionFactor, feedPrice,
                        workerSalary, amountWorkers, cwsdCapacity,
                        electricityCost, rent, costCWSD, depreciationReservePercent,
                        expansionReservePercent, credit, annualPercentage, amountCreditMonth,
                        grant, fishPrice, massCommercialFish)
            cwsd.work_cwsd(startDate, endDate, reserve, deltaMass, minMass, maxMass)
            x = cwsd.calculate_result_business_plan(startDate, endDate, limitSalary)
            print(i, ' результат: ', x)
            result += x

        return result / amountSteps

    def calculate_min_of_max_mass_fry(self, startDate, endDate, startMaxMass, step, endMaxMass):
        maxMass = startMaxMass
        max = 0
        result = maxMass
        encounter = 1
        while (maxMass <= endMaxMass):
            x = self._calculate_average_profit(startDate, endDate, 5, 50,
                                               50, 20, maxMass, 100000, self.masses, self.mainVolueFish)
            if (max < x):
                max = x
                result = maxMass
            draw_line(startMaxMass, endMaxMass, step, encounter)
            maxMass += step
            print([maxMass, x])
            encounter += 1
        return [result, max]


class Module():
    costCWSD = 3000000
    amountPools = 0
    # температура воды
    temperature = 21
    # арендная плата
    rent = 70000
    # стоимость киловатт в час
    costElectricityPerHour = 3.17
    # мощность узв
    equipmentCapacity = 5.6
    # стоимость корма
    feedPrice = 260
    onePoolSquare = 0
    correctionFactor = 2
    pools = list()
    poolsInfo = list()
    masses = list()


    def __init__(self, poolSquare, masses, amountPools=4, correctionFactor=2, singleVolumeFish=100,
                 fishPrice=850, massComercialFish=400, maximumPlantingDensity=40):
        self.onePoolSquare = poolSquare
        self.amountPools = amountPools
        self.correctionFactor = correctionFactor

        self.pools = list()
        self.poolsInfo = list()
        self.masses = masses

        for i in range(amountPools):
            pool = Pool(poolSquare, singleVolumeFish, fishPrice, massComercialFish, maximumPlantingDensity)
            self.pools.append(pool)

    def add_biomass_in_pool(self, poolNumber, amountFishes, mass, newIndex, date):
        self.pools[poolNumber].add_new_biomass(amountFishes, mass, newIndex, date)

    def move_fish_from_one_pool_to_another(self, onePoolNumber, anotherPoolNumber, amountMovedFish):
        # удалим выросшую рыбу из старого бассейна
        removedFish = self.pools[onePoolNumber].arrayFishes.remove_biomass(amountMovedFish)
        # обновим плотность
        self.pools[onePoolNumber].update_density()
        # добавим удаленную рыбу в другой бассейн
        self.pools[anotherPoolNumber].arrayFishes.add_other_FishArrays(removedFish)
        # обновим плотность в другом бассейне
        self.pools[anotherPoolNumber].update_density()
        # теперь в новом бассейне плавает малек с индексом из предыдущего басса
        self.pools[anotherPoolNumber].indexFry = self.pools[onePoolNumber].indexFry

    def total_daily_work(self, day, save_pool_info):
        for i in range(self.amountPools):
            self.pools[i].daily_growth(day, save_pool_info)

    def print_info(self):
        print()
        for i in range(self.amountPools):
            print('№', i, ' бассейн, indexFry = ', self.pools[i].indexFry, ', количество рыбы = ',
                  self.pools[i].arrayFishes.get_amount_fishes(),
                  ', биомасса = ', self.pools[i].arrayFishes.get_biomass(),
                  ', средняя масса = ', self.pools[i].arrayFishes.calculate_average_mass(),
                  ', плотность = ', self.pools[i].update_density())
            if (self.pools[i].arrayFishes.get_amount_fishes() != 0):
                # выпишем данные о первых amoutItemes рыбках
                print(self.pools[i].arrayFishes.get_three_fish())
            else:
                print('Рыбы нет')
        print('_______________________________________________________')

    def find_optimal_fry_mass(self, minMass, maxMass, deltaMass):
        minAverageMass = 10000
        for i in range(self.amountPools):
            averageMassInThisPool = self.pools[i].arrayFishes.calculate_average_mass()
            if ((minAverageMass > averageMassInThisPool) and (averageMassInThisPool > 0)):
                minAverageMass = averageMassInThisPool

        result = (int((minAverageMass - deltaMass) / 10)) * 10
        if (result < minMass):
            result = minMass
        elif(result > maxMass):
            result = maxMass

        return result

    def find_empty_pool_and_add_one_volume(self, volumeFish, newIndex, day, deltaMass, minMass, maxMass):
        emptyPool = 0
        for i in range(self.amountPools):
            if (self.pools[i].arrayFishes.get_amount_fishes() == 0):
                emptyPool = i

        optimalMass = self.find_optimal_fry_mass(minMass, maxMass, deltaMass)
        self.pools[emptyPool].add_new_biomass(volumeFish, optimalMass, newIndex, day)

    def find_empty_pool_and_add_twice_volume(self, volumeFish, newIndex, day, koef, deltaMass, minMass, maxMass):
        emptyPool = 0
        for i in range(self.amountPools):
            if (self.pools[i].arrayFishes.get_amount_fishes() == 0):
                emptyPool = i
                break

        optimalMass = self.find_optimal_fry_mass(minMass, maxMass, deltaMass)
        self.pools[emptyPool].add_new_biomass(int(koef * volumeFish), optimalMass, newIndex, day)

    def find_pool_with_twice_volume_and_move_half_in_empty(self):
        overflowingPool = 0
        emptyPool = 0
        maxAmount = 0
        volumeFish = 0
        for i in range(self.amountPools):
            if (self.pools[i].arrayFishes.get_amount_fishes() > maxAmount):
                overflowingPool = i
                maxAmount = self.pools[i].arrayFishes.get_amount_fishes()

            volumeFish = int(maxAmount / 2)

            if (self.pools[i].arrayFishes.get_amount_fishes() == 0):
                emptyPool = i

        self.move_fish_from_one_pool_to_another(overflowingPool, emptyPool, volumeFish)

    def grow_up_fish_in_one_pool(self, startDay, startDateSaving):
        flag = True
        day = startDay
        currentDateSaving = startDateSaving

        while (flag):
            while (currentDateSaving < day):
                currentDateSaving = calculate_end_date_of_month(currentDateSaving)

            if (currentDateSaving == day):
                needSave = True
                currentDateSaving = calculate_end_date_of_month(currentDateSaving)
            else:
                needSave = False

            self.total_daily_work(day, needSave)
            day += date.timedelta(1)
            for i in range(self.amountPools):
                if (self.pools[i].arrayFishes.get_amount_fishes() == 0):
                    flag = False
                    break

        return day

    def grow_up_fish_in_two_pools(self, startDay, startDateSaving):
        flag = True
        day = startDay
        currentDateSaving = startDateSaving

        while(flag):
            while (currentDateSaving < day):
                currentDateSaving = calculate_end_date_of_month(currentDateSaving)

            if (currentDateSaving == day):
                needSave = True
                currentDateSaving = calculate_end_date_of_month(currentDateSaving)
                x = currentDateSaving
                y = day

            else:
                needSave = False

            self.total_daily_work(day, needSave)
            day += date.timedelta(1)

            amountEmptyPools = 0
            for i in range(self.amountPools):
                if (self.pools[i].arrayFishes.get_amount_fishes() == 0):
                    amountEmptyPools += 1

            if (amountEmptyPools >= 2):
                flag = False

        return day

    def start_script1(self, reserve, startDate, koef, deltaMass, minMass, maxMass, mainVolumeFish):
        mainVolumeFish -= reserve

        for i in range(self.amountPools - 1):
            self.pools[i].add_new_biomass(mainVolumeFish, self.masses[i], i, startDate)
        # в бассейн с самой легкой рыбой отправляем в koef раз больше
        self.pools[self.amountPools - 1].indexFry = self.amountPools - 1
        self.pools[self.amountPools - 1].add_new_biomass(int(koef * mainVolumeFish), self.masses[self.amountPools - 1],
                                                          self.amountPools - 1, startDate)

        day = startDate

        # вырастим рыбу в 0 бассейне
        day = self.grow_up_fish_in_one_pool(day, startDate)

        # переместим рыбу из 3 в 0 бассейн
        self.find_pool_with_twice_volume_and_move_half_in_empty()

        # вырастим рыбу в 1 бассейне
        day = self.grow_up_fish_in_one_pool(day, startDate)

        currentIndex = 4

        # добавим рыбу 2 * mainValue в 1 бассейн
        self.find_empty_pool_and_add_twice_volume(mainVolumeFish, currentIndex, day, koef, deltaMass, minMass, maxMass)
        currentIndex += 1

        # вырастим рыбу в 2 бассейне
        day = self.grow_up_fish_in_one_pool(day, startDate)

        return [mainVolumeFish, day, currentIndex]

    def main_script1(self, mainValue, day, previousIndex, startDateSaving, koef, deltaMass, minMass, maxMass):
        # переместим из переполненного бассейна в пустой половину
        self.find_pool_with_twice_volume_and_move_half_in_empty()

        # вырастим рыбу в 2 бассейнах
        day = self.grow_up_fish_in_two_pools(day, startDateSaving)

        currentIndex = previousIndex
        # добавим mainValue штук рыб в пустой бассейн
        self.find_empty_pool_and_add_one_volume(mainValue, currentIndex, day, deltaMass, minMass, maxMass)
        currentIndex += 1

        # добавим koef * mainValue штук рыб в другой пустой бассейн
        self.find_empty_pool_and_add_twice_volume(mainValue, currentIndex, day, koef, deltaMass, minMass, maxMass)
        currentIndex += 1

        # вырастим рыбу в 2 бассейнах
        day = self.grow_up_fish_in_two_pools(day, startDateSaving)

        # переместим из переполненного бассейна в пустой
        self.find_pool_with_twice_volume_and_move_half_in_empty()

        # добавим 2 * mainValue штук рыб в другой пустой бассейн
        self.find_empty_pool_and_add_twice_volume(mainValue, currentIndex, day, koef, deltaMass, minMass, maxMass)
        currentIndex += 1

        # вырастим рыбу в 1 бассейне
        day = self.grow_up_fish_in_one_pool(day, startDateSaving)

        return [mainValue, day, currentIndex]

    def main_work1(self, startDate, endDate, reserve, deltaMass, minMass, maxMass, mainVolumeFish):
        resultStartScript = self.start_script1(reserve, startDate, self.correctionFactor,
                                               deltaMass, minMass, maxMass, mainVolumeFish)

        day = resultStartScript[1]
        # [mainVolumeFish, day, currentIndex]
        resultMainScript = self.main_script1(resultStartScript[0],
                                             resultStartScript[1],
                                             resultStartScript[2],
                                             startDate, self.correctionFactor, deltaMass, minMass, maxMass)

        numberMainScript = 2
        while (day < endDate):
            numberMainScript += 1
            # [mainValue, day, currentIndex]
            resultMainScript = self.main_script1(resultMainScript[0],
                                                 resultMainScript[1],
                                                 resultMainScript[2],
                                                 startDate, self.correctionFactor, deltaMass, minMass, maxMass)
            day = resultMainScript[1]

    def start_script_with_print(self, reserve, startDate, koef, deltaMass, minMass, maxMass, mainVolumeFish):
        mainVolumeFish -= reserve
        print('Оптимальное количество мальков в 1 бассейн: ', mainVolumeFish)

        print('Сделаем первое зарыбление ', startDate)
        for i in range(self.amountPools - 1):
            self.pools[i].add_new_biomass(mainVolumeFish, self.masses[i], i, startDate)
        # в бассейн с самой легкой рыбой отправляем в koef раз больше
        self.pools[self.amountPools - 1].indexFry = self.amountPools - 1
        self.pools[self.amountPools - 1].add_new_biomass(int(koef * mainVolumeFish), self.masses[self.amountPools - 1],
                                                         self.amountPools - 1, startDate)
        self.print_info()

        day = startDate

        # вырастим рыбу в 0 бассейне
        print('вырастим рыбу в 0 бассейне')
        day = self.grow_up_fish_in_one_pool(day, startDate)
        print(day)
        self.print_info()

        # переместим рыбу из 3 в 0 бассейн
        print('переместим рыбу из 3 в 0 бассейн')
        self.find_pool_with_twice_volume_and_move_half_in_empty()
        self.print_info()

        # вырастим рыбу в 1 бассейне
        print('вырастим рыбу в 1 бассейне')
        day = self.grow_up_fish_in_one_pool(day, startDate)
        print(day)
        self.print_info()

        currentIndex = 4

        # добавим рыбу 2 * mainValue в 1 бассейн
        print('добавим рыбу 2 * mainValue в 1 бассейн')
        self.find_empty_pool_and_add_twice_volume(mainVolumeFish, currentIndex, day, koef, deltaMass, minMass, maxMass)
        self.print_info()
        currentIndex += 1

        # вырастим рыбу в 2 бассейне
        print('вырастим рыбу в 2 бассейне')
        day = self.grow_up_fish_in_one_pool(day, startDate)
        print(day)
        self.print_info()

        return [mainVolumeFish, day, currentIndex]

    def main_script_with_print(self, mainValue, day, previousIndex, startDateSaving,
                               koef, deltaMass, minMass, maxMass):
        # переместим из переполненного бассейна в пустой половину
        print('переместим из переполненного бассейна в пустой половину')
        self.find_pool_with_twice_volume_and_move_half_in_empty()
        self.print_info()

        # вырастим рыбу в 2 бассейнах
        print('вырастим рыбу в 2 бассейнах')
        day = self.grow_up_fish_in_two_pools(day, startDateSaving)
        print(day)
        self.print_info()

        currentIndex = previousIndex
        # добавим mainValue штук рыб в пустой бассейн
        print('добавим mainValue штук рыб в пустой бассейн')
        self.find_empty_pool_and_add_one_volume(mainValue, currentIndex, day, deltaMass, minMass, maxMass)
        self.print_info()
        currentIndex += 1

        # добавим koef * mainValue штук рыб в другой пустой бассейн
        print('добавим koef * mainValue штук рыб в другой пустой бассейн')
        self.find_empty_pool_and_add_twice_volume(mainValue, currentIndex, day, koef, deltaMass, minMass, maxMass)
        currentIndex += 1
        self.print_info()

        # вырастим рыбу в 2 бассейнах
        print('вырастим рыбу в 2 бассейнах')
        day = self.grow_up_fish_in_two_pools(day, startDateSaving)
        print(day)
        self.print_info()

        # переместим из переполненного бассейна в пустой
        print('переместим из переполненного бассейна в пустой')
        self.find_pool_with_twice_volume_and_move_half_in_empty()
        self.print_info()

        # добавим 2 * mainValue штук рыб в другой пустой бассейн
        print('добавим 2 * mainValue штук рыб в другой пустой бассейн')
        self.find_empty_pool_and_add_twice_volume(mainValue, currentIndex, day, koef, deltaMass, minMass, maxMass)
        self.print_info()
        currentIndex += 1

        # вырастим рыбу в 1 бассейне
        print('вырастим рыбу в 1 бассейне')
        day = self.grow_up_fish_in_one_pool(day, startDateSaving)
        print(day)
        self.print_info()

        return [mainValue, day, currentIndex]

    def main_work_with_print(self, startDate, endDate, reserve, deltaMass, minMass, maxMass, mainVolumeFish):
        resultStartScript = self.start_script_with_print(reserve, startDate, self.correctionFactor,
                                                         deltaMass, minMass, maxMass, mainVolumeFish)

        day = resultStartScript[1]
        # [mainVolumeFish, day, currentIndex]
        resultMainScript = self.main_script_with_print(resultStartScript[0],
                                             resultStartScript[1],
                                             resultStartScript[2],
                                             startDate, self.correctionFactor, deltaMass, minMass, maxMass)

        numberMainScript = 2
        while (day < endDate):
            numberMainScript += 1
            # [mainValue, day, currentIndex]
            resultMainScript = self.main_script_with_print(resultMainScript[0],
                                                 resultMainScript[1],
                                                 resultMainScript[2],
                                                 startDate, self.correctionFactor, deltaMass, minMass, maxMass)
            day = resultMainScript[1]


class CWSD():
    amountModules = 0
    amountPools = 0
    modules = list()
    square = 0
    salary = 0
    amountWorkers = 0
    equipmentCapacity = 0.0
    rent = 0
    costElectricity = 0
    costCWSD = 0
    feedPrice = 0
    depreciationReservePercent = 0.0
    expansionReservePercent = 0.0
    depreciationReserve = 0
    expansionReserve = 0
    expensesReserve = 0
    principalDebt = 0
    annualPercentage = 0.0
    amountMonth = 0
    grant = 0
    mainVolumeFish = 0
    costNewCWSD = 0
    costFixingCar = 0
    depreciationLimit = 0
    # финансовая подушка
    financialCushion = 0

    feedings = list()
    fries = list()
    salaries = list()
    rents = list()
    electricities = list()
    revenues = list()
    resultBusinessPlan = list()

    monthlyPayment = 0


    def __init__(self, masses, mainVolumeFish, amountModules=2, amountPools=4, square=10,
                 correctionFactor=2,feedPrice=260, salary=30000,
                 amountWorkers=2, equipmentCapacity=5.5, costElectricity=3.17, rent=100000,
                 costCWSD=0, depreciationReservePercent=10.0, expansionReservePercent=10.0,
                 principalDebt=500000, annualPercentage=15.0, amountMonth=12, grant=5000000,
                 fishPrice=850, massCommercialFish=400, singleVolumeFish=100, maximumPlantingDensity=40,
                 costFixingCar=300000, costNewCWSD=5500000, financialCushion=300000):
        self.amountModules = amountModules
        self.mainVolumeFish = mainVolumeFish
        self.feedPrice = feedPrice
        self.financialCushion = financialCushion
        self.modules = list()
        for i in range(amountModules):
            module = Module(square, masses, amountPools, correctionFactor,
                            singleVolumeFish, fishPrice, massCommercialFish,
                            maximumPlantingDensity)
            self.modules.append(module)

        self.amountPools = amountPools
        self.salary = salary
        self.amountWorkers = amountWorkers
        self.equipmentCapacity = equipmentCapacity
        self.costElectricity = costElectricity
        self.rent = rent
        self.costCWSD = costCWSD
        self.depreciationReservePercent = depreciationReservePercent
        self.expansionReservePercent = expansionReservePercent
        self.depreciationReserve = 0
        self.expansionReserve = 0
        self.principalDebt = principalDebt
        self.annualPercentage = annualPercentage
        self.amountMonth = amountMonth
        self.grant = grant

        self.feedings = list()
        self.fries = list()
        self.salaries = list()
        self.rents = list()
        self.electricities = list()
        self.revenues = list()
        self.resultBusinessPlan = list()

        self.depreciationLimit = 1.5 * (self.costCWSD + costFixingCar)
        self.costNewCWSD = costNewCWSD

    def _calculate_all_casts_and_profits_for_all_period(self, startDate, endDate):
        for i in range(self.amountModules):
            for j in range(self.amountPools):
                for k in range(len(self.modules[i].pools[j].feeding)):
                    # [day, todayFeedMass]
                    self.feedings.append([self.modules[i].pools[j].feeding[k][0],
                                          self.modules[i].pools[j].feeding[k][1] * self.feedPrice])
                for k in range(len(self.modules[i].pools[j].arrayFryPurchases)):
                    # [date, amountFishes, averageMass, totalPrice]
                    self.fries.append([self.modules[i].pools[j].arrayFryPurchases[k][0],
                                      self.modules[i].pools[j].arrayFryPurchases[k][3]])
                for k in range(len(self.modules[i].pools[j].arraySoldFish)):
                    # [day, amountSoldFish, soldBiomass, revenue]
                    self.revenues.append([self.modules[i].pools[j].arraySoldFish[k][0],
                                          self.modules[i].pools[j].arraySoldFish[k][3]])

        startMonth = startDate
        endMonth = calculate_end_date_of_month(startMonth) - date.timedelta(1)
        while (endMonth <= endDate):
            self.rents.append([endMonth, self.rent])
            self.salaries.append([endMonth, self.amountWorkers * self.salary])
            amountDaysInThisMonth = (endMonth - startMonth).days
            self.electricities.append([endMonth,
                                      amountDaysInThisMonth * 24 * self.equipmentCapacity * self.costElectricity])
            startMonth = endMonth + date.timedelta(1)
            endMonth = calculate_end_date_of_month(startMonth) - date.timedelta(1)

    def work_cwsd(self, startDate, endDate, reserve, deltaMass, minMass, maxMass):
        for i in range(self.amountModules):
            self.modules[i].main_work1(startDate, endDate, reserve, deltaMass, minMass, maxMass, self.mainVolumeFish)

        self._calculate_all_casts_and_profits_for_all_period(startDate, endDate)

    def work_cwsd_with_print(self, startDate, endDate, reserve, deltaMass, minMass, maxMass):
        for i in range(self.amountModules):
            self.modules[i].main_work_with_print(startDate, endDate, reserve,
                                                 deltaMass, minMass, maxMass, self.mainVolumeFish)

        self._calculate_all_casts_and_profits_for_all_period(startDate, endDate)

    def _find_events_in_this_period(self, array, startPeriod, endPeriod):
        result = 0
        for i in range(len(array)):
            if (startPeriod <= array[i][0] < endPeriod):
                result += array[i][1]
        return result

    def _find_event_on_this_day(self, array, day):
        result = 0
        for i in range(len(array)):
            if (array[i][0] == day):
                result += array[i][1]
        return result

    def calculate_result_business_plan(self, startDate, endDate, limitSalary):
        startMonth = startDate
        endMonth = calculate_end_date_of_month(startMonth)
        self.expensesReserve = self.principalDebt + self.grant - self.costCWSD
        self.depreciationReserve = 0
        self.expansionReserve = 0
        self.calculate_monthly_loan_payment()
        currentMonth = 1
        maxGeneralExpenses = 0

        while(endMonth <= endDate):
            item = [endMonth, self.expensesReserve, self.expansionReserve]
            bioCost_fries = self._find_events_in_this_period(self.fries, startMonth, endMonth)
            item.append(bioCost_fries)
            bioCost_feedings = self._find_events_in_this_period(self.feedings, startMonth, endMonth)
            item.append(bioCost_feedings)
            techCost_salaries = self._find_events_in_this_period(self.salaries, startMonth, endMonth)
            item.append(techCost_salaries)
            techCost_rents = self._find_events_in_this_period(self.rents, startMonth, endMonth)
            item.append(techCost_rents)
            techCost_electricities = self._find_events_in_this_period(self.electricities, startMonth, endMonth)
            item.append(techCost_electricities)
            revenue = self._find_events_in_this_period(self.revenues, startMonth, endMonth)
            item.append(revenue)

            generalExpenses = 0
            if (currentMonth <= self.amountMonth):
                generalExpenses += self.monthlyPayment
                currentMonth += 1
            else:
                self.monthlyPayment = 0

            generalExpenses += bioCost_fries + bioCost_feedings + techCost_salaries\
                                             + techCost_rents + techCost_electricities\
                                             + self.monthlyPayment

            if (generalExpenses > maxGeneralExpenses):
                maxGeneralExpenses = generalExpenses

            currentProfit = revenue - generalExpenses
            currentSallary = 0
            if ((currentProfit > 0) and
                    (self.expensesReserve + currentProfit > maxGeneralExpenses + self.financialCushion)):
                delta = self.expensesReserve + currentProfit - (maxGeneralExpenses + self.financialCushion)
                if (delta > 2 * limitSalary):
                    currentSallary = 2 * limitSalary
                else:
                    currentSallary = 0.5 * delta

                rest = delta - currentSallary
                self.expansionReserve

            item.append(currentBudget)
            item.append(0)
            item.append(0)
            item.append(self.monthlyPayment)
            item.append(generalExpenses)

            # item = [конец этого месяца, предыдущий бюджет, траты на мальков,
            #         на корм, на зарплату, на аренду, на электричество, выручка, текущий бюджет,
            #         резерв на амортизацию, резерв на расширение, месячная плата за кредит, общие расходы]
            self.resultBusinessPlan.append(item)
            startMonth = endMonth
            endMonth = calculate_end_date_of_month(startMonth)

        return self.resultBusinessPlan[len(self.resultBusinessPlan) - 1][9] + \
               self.resultBusinessPlan[len(self.resultBusinessPlan) - 1][10]

    def find_minimal_budget(self):
        # item = [конец этого месяца, предыдущий бюджет, траты на мальков,
        #         на корм, на зарплату, на аренду, на электричество, выручка, текущий бюджет,
        #         резерв на амортизацию, резерв на расширение]
        result = self.resultBusinessPlan[0][8]
        for i in range(len(self.resultBusinessPlan)):
            if (result > self.resultBusinessPlan[i][8]):
                result = self.resultBusinessPlan[i][8]
        return result

    def print_info(self, startDate):
        startMonth = startDate

        for i in range(len(self.resultBusinessPlan)):
            item = self.resultBusinessPlan[i]
            # item = [конец этого месяца, предыдущий бюджет, траты на мальков,
            #         на корм, на зарплату, на аренду, на электричество, выручка, текущий бюджет,
            #         резерв на амортизацию оборудования, резерв на расширение]
            print('------------------------------------------------------------')
            print(i, ' месяц, с ', startMonth, ' по ', item[0])
            print('На конец текущего месяца ситуация в бассейнах будет следующая:')
            for j in range(self.amountModules):
                for k in range(self.amountPools):
                    # [день, количество рыбы, биомасса, средняя масса, плотность]
                    print(j * self.amountPools + k, ' бассейн, количество мальков: ',
                          self.modules[j].pools[k].poolHistory[i][1], ' биомасса: ',
                          self.modules[j].pools[k].poolHistory[i][2], ' средняя масса: ',
                          self.modules[j].pools[k].poolHistory[i][3], ' плотность посадки: ',
                          self.modules[j].pools[k].poolHistory[i][4])
            print('Бюджет с прошлого месяца: ', item[1])
            print('Будет затрачено на мальков: ', item[2])
            print('На корм: ', item[3])
            print('На зарплату: ', item[4])
            print('На аренду: ', item[5])
            print('На электричество: ', item[6])
            print('Выплаты за кредит: ', item[11])

            print('Общие расходы: ', item[12])
            print('Резерв на амортизацию оборудования составляет: ', item[9])
            print('Резерв на расширение производства составляет: ', item[10])
            print('Выручка составит: ', item[7])
            print('Бюджет на конец текущего месяца месяца составит: ', item[8])
            print()
            startMonth = item[0]

    def calculate_monthly_loan_payment(self):
        monthlyPercentage = self.annualPercentage / 12 / 100
        annuityRatio = monthlyPercentage * (1 + monthlyPercentage) ** self.amountMonth
        annuityRatio /= (1 + monthlyPercentage) ** self.amountMonth - 1
        monthlyPayment = self.principalDebt * annuityRatio
        self.monthlyPayment = monthlyPayment


class Business():
    cwsds = list()
    amountCWSDs = 0
    startMasses = list()
    totalBudget = 0

    def __init__(self, startMasses):
        self.cwsds = list()
        self.startMasses = startMasses
        self.amountCWSDs = 0
        self.totalBudget = 0

    def addNewCWSD(self, masses, mainVolumeFish, amountModules, amountPools,
                   poolSquare, correctionFactor, feedPrice,
                   workerSalary, amountWorkers, cwsdCapacity,
                   electricityCost, rent, costCWSD, depreciationReservePercent,
                   expansionReservePercent, credit, annualPercentage, amountCreditMonth,
                   grant, fishPrice, massCommercialFish):

        self.amountCWSDs += 1
        newCWSD = CWSD(masses, mainVolumeFish, amountModules, amountPools,
                       poolSquare, correctionFactor, feedPrice,
                       workerSalary, amountWorkers, cwsdCapacity,
                       electricityCost, rent, costCWSD, depreciationReservePercent,
                       expansionReservePercent, credit, annualPercentage, amountCreditMonth,
                       grant, fishPrice, massCommercialFish)
        self.cwsds.append(newCWSD)

    def work_cwsd(self, cwsdNumber, minMass, maxMass):
        self.cwsds[cwsdNumber].work_cwsd_with_print(date.date.today(), date.date(2028, 1, 1), 50, 50, minMass, maxMass)
        self.cwsds[cwsdNumber].calculate_result_business_plan(date.date.today(), date.date(2028, 1, 1), 100000)

    def make_business_plan(self):
        pass


masses = [100, 50, 30, 20]
amountModules = 2
amountPools = 4
poolSquare = 10
# показывает во сколько ра нужно переполнить бассейн
correctionFactor = 2
feedPrice = 260
massCommercialFish = 400
fishPrice = 850
workerSalary = 40000
amountWorkers = 2
cwsdCapacity = 5.5
electricityCost = 3.17
rent = 100000
costCWSD = 3000000
depreciationReservePercent = 7.5
expansionReservePercent = 7.5
credit = 500000
annualPercentage = 15
amountCreditMonth = 12
grant = 5000000
feedRatio = 1.5

opt = Opimization(masses, 730, amountModules, amountPools,
                  poolSquare, correctionFactor, feedPrice,
                  workerSalary, amountWorkers, cwsdCapacity,
                  electricityCost, rent, costCWSD, depreciationReservePercent,
                  expansionReservePercent, credit, annualPercentage, amountCreditMonth,
                  grant, fishPrice, massCommercialFish)

optimalQuantity = opt.calculate_optimized_amount_fish_in_commercial_pool(poolSquare,
                                                                         masses[amountPools - 1],
                                                                         masses[amountPools - 1],
                                                                         10, 10)
mainVolumeFish = optimalQuantity[0]
opt.mainVolumeFish = mainVolumeFish

cwsd = CWSD(masses, mainVolumeFish, amountModules, amountPools,
            poolSquare, correctionFactor, feedPrice,
            workerSalary, amountWorkers, cwsdCapacity,
            electricityCost, rent, costCWSD, depreciationReservePercent,
            expansionReservePercent, credit, annualPercentage, amountCreditMonth,
            grant, fishPrice, massCommercialFish)

cwsd.work_cwsd_with_print(date.date.today(), date.date(2028, 6, 1), 50, 50, 20, 250)
cwsd.calculate_result_business_plan(date.date.today(), date.date(2028, 6, 1), 100000)
cwsd.print_info(date.date.today())
print(cwsd.find_minimal_budget())
